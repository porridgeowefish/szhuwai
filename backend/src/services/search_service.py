"""
搜索服务
========

封装网络搜索逻辑。
"""

import json
import re
from typing import List

import requests

from loguru import logger

from src.schemas.search import SearchEmergencyContact, WebSearchInsight, WebSearchResponse
from src.api.search_client import SearchClient


class SearchService:
    """搜索服务"""

    def __init__(self, config=None):
        """初始化服务"""
        self.client = SearchClient(config)

    def search(
        self,
        keywords: str,
        search_types: List[str] = None,
        max_results: int = 5
    ) -> List[WebSearchResponse]:
        """
        执行多维度搜索

        Args:
            keywords: 搜索关键词
            search_types: 搜索类型列表，默认为 ['景点', '救援', '攻略', '装备']
            max_results: 每组搜索的最大结果数

        Returns:
            List[WebSearchResponse]: 搜索结果列表
        """
        if search_types is None:
            search_types = ['景点', '救援', '攻略', '装备']

        # 构建搜索查询
        search_queries = self._build_search_queries(keywords, search_types)
        logger.info(f"搜索关键词: {keywords}, 类型: {search_types}")

        all_results = []
        for query in search_queries:
            try:
                logger.info(f"执行搜索查询: {query}")
                result = self.client.search(query, max_results=max_results)
                if result and isinstance(result, WebSearchResponse):
                    all_results.append(result)
            except Exception as e:
                logger.error(f"搜索失败 [{query}]: {e}")
                continue

        return all_results

    def search_with_insight(
        self,
        keywords: str,
        search_types: List[str] = None,
        max_results: int = 5,
        local_context: list[str] | None = None,
    ) -> tuple[List[WebSearchResponse], WebSearchInsight]:
        """搜索并提炼为报告可读的沿途风光/攻略/应急摘要。

        LLM 失败时降级为本地摘要，主流程不因 AI 阻塞。
        """
        responses = self.search(keywords, search_types, max_results)
        insight = self._summarize_with_llm(keywords, responses, local_context or [])
        if not insight.summary:
            insight = self._fallback_insight(responses, local_context or [])
        return responses, insight

    def _build_search_queries(self, keywords: str, search_types: List[str]) -> List[str]:
        """构建搜索查询列表"""
        queries = []
        platform_filter = "(site:www.baidu.com OR site:douyin.com OR site:bilibili.com OR site:xiaohongshu.com)"

        if '景点' in search_types:
            queries.append(f"{keywords} 景点 景区 旅游 {platform_filter}")

        if '救援' in search_types:
            queries.append(f"{keywords} 户外徒步 应急救援队 报警电话 {platform_filter}")

        if '攻略' in search_types:
            queries.append(f"{keywords} 徒步攻略 登山路线 注意事项 {platform_filter}")

        if '装备' in search_types:
            queries.append(f"{keywords} 徒步装备 登山装备 露营装备推荐 {platform_filter}")

        return queries

    def _summarize_with_llm(
        self,
        keywords: str,
        responses: List[WebSearchResponse],
        local_context: list[str],
    ) -> WebSearchInsight:
        """调用 OpenAI-compatible LLM 做保守摘要。"""
        config = self.client.config
        if not config.LLM_API_KEY:
            return WebSearchInsight()

        materials = self._format_search_materials(responses)
        if not materials:
            return WebSearchInsight()

        system_prompt = (
            "你是户外行前信息核验助手。必须仅基于用户提供的搜索材料回答，"
            "严禁捏造、补全或使用材料之外的信息。没有可靠信息时写“未检索到可靠信息”。"
            "输出 JSON，不要 Markdown。"
        )
        user_prompt = (
            f"线路关键词：{keywords}\n"
            "请从材料中提炼：1）沿途风光/地貌/人文线索；2）实际攻略要点；"
            "3）应急电话或救援机构。多个相同电话只保留一个。\n"
            "JSON 格式：{\"summary\":\"不超过220字\","
            "\"emergency_contacts\":[{\"name\":\"机构名\",\"phone\":\"电话\",\"contact_type\":\"医疗/救援/报警\"}]}\n"
            f"高德逆地理/周边景观线索：{'；'.join(local_context[:12]) or '无'}\n"
            f"搜索材料：\n{materials}"
        )

        try:
            response = requests.post(
                f"{config.LLM_BASE_URL.rstrip('/')}/chat/completions",
                headers=config.get_headers("llm"),
                json={
                    "model": config.LLM_MODEL,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "temperature": config.LLM_TEMPERATURE,
                    "max_tokens": min(config.LLM_MAX_TOKENS, 1200),
                    "response_format": {"type": "json_object"},
                },
                timeout=min(config.LLM_TIMEOUT, 90),
                proxies=config.PROXY if config.should_use_proxy() else {"http": None, "https": None},
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            data = json.loads(content)
            return WebSearchInsight(
                summary=str(data.get("summary", "")).strip(),
                emergency_contacts=[
                    SearchEmergencyContact(
                        name=str(item.get("name", "")).strip() or "网络检索电话",
                        phone=str(item.get("phone", "")).strip(),
                        contact_type=str(item.get("contact_type", "救援")).strip() or "救援",
                    )
                    for item in data.get("emergency_contacts", [])
                    if isinstance(item, dict) and str(item.get("phone", "")).strip()
                ],
            )
        except Exception as exc:  # noqa: BLE001 - AI 摘要失败需要降级，不影响主流程
            logger.warning(f"AI 搜索摘要失败，降级为本地摘要: {exc}")
            return WebSearchInsight()

    def _fallback_insight(self, responses: List[WebSearchResponse], local_context: list[str]) -> WebSearchInsight:
        snippets: list[str] = []
        contacts: list[SearchEmergencyContact] = []
        seen_phones: set[str] = set()
        for response in responses:
            for result in response.results:
                text = " ".join(part for part in [result.title, result.content] if part)
                if text and len(snippets) < 3:
                    snippets.append(text[:90])
                for phone in self._extract_phone_numbers(text):
                    if phone in seen_phones:
                        continue
                    seen_phones.add(phone)
                    contacts.append(SearchEmergencyContact(
                        name=result.title[:40] or "网络检索电话",
                        phone=phone,
                        contact_type="救援",
                    ))
        summary_parts = []
        if local_context:
            summary_parts.append("高德周边线索：" + "、".join(local_context[:6]))
        if snippets:
            summary_parts.append("网络资料摘要：" + "；".join(snippets))
        summary = "；".join(summary_parts)
        return WebSearchInsight(summary=summary, emergency_contacts=contacts[:6])

    def _format_search_materials(self, responses: List[WebSearchResponse]) -> str:
        lines: list[str] = []
        index = 1
        for response in responses:
            for result in response.results[:5]:
                text = result.raw_content or result.content
                text = " ".join(text.split())[:900]
                if not text:
                    continue
                lines.append(f"{index}. 标题：{result.title}\n来源：{result.source}\nURL：{result.url}\n内容：{text}")
                index += 1
                if index > 12:
                    return "\n\n".join(lines)
        return "\n\n".join(lines)

    @staticmethod
    def _extract_phone_numbers(text: str) -> list[str]:
        """提取常见中国大陆电话，过滤过短噪声。"""
        phones = re.findall(r"(?<!\d)(?:0\d{2,3}[- ]?\d{7,8}|1[3-9]\d{9}|1[1209]{2})(?!\d)", text)
        cleaned: list[str] = []
        for phone in phones:
            normalized = re.sub(r"\s+", "", phone)
            digits = re.sub(r"\D", "", normalized)
            if len(digits) < 3:
                continue
            cleaned.append(normalized)
        return cleaned
