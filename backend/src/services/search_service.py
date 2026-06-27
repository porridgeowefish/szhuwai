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

from src.schemas.output import WebReference
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

    def synthesize_insight(
        self,
        keywords: str,
        responses: List[WebSearchResponse],
        local_context: list[str] | None = None,
    ) -> WebSearchInsight:
        """把搜索结果 + 高德周边线索统一交给 LLM 过滤提炼为行前洞察。

        - 高德线索也在此一并交给 LLM 消化（而非调用方硬拼），避免 POI 等术语外漏；
        - LLM 不可用或失败时降级为本地摘要，绝不抛错，不阻塞主流程。
        """
        ctx = [self._clean_term(c) for c in (local_context or []) if c and c.strip()]
        insight = self._summarize_with_llm(keywords, responses, ctx)
        if not insight.summary:
            insight = self._fallback_insight(responses, ctx)
        return insight

    def synthesize_from_references(
        self,
        keywords: str,
        references: List[WebReference],
    ) -> WebSearchInsight:
        """主结果返回后的异步补充：基于前端回传的网络参考资料调 LLM 提炼摘要。

        与 synthesize_insight 的区别：输入是 WebReference（标题+摘要）而非完整搜索响应，
        且不携带高德景观线索（减少噪音）。LLM 不可用/失败时用参考摘要简单拼接降级。
        """
        materials = self._format_references(references)
        insight = self._llm_synthesize(keywords, materials, [])
        if not insight.summary:
            snippets = [r.snippet for r in references[:3] if r.snippet]
            insight = WebSearchInsight(summary="；".join(snippets))
        return insight

    def _build_search_queries(self, keywords: str, search_types: List[str]) -> List[str]:
        """构建搜索查询列表"""
        queries = []
        platform_filter = "(site:www.baidu.com OR site:douyin.com OR site:xiaohongshu.com)"

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
        """对完整搜索响应格式化后交给 LLM 提炼。"""
        materials = self._format_search_materials(responses)
        if not materials:
            return WebSearchInsight()
        return self._llm_synthesize(keywords, materials, local_context)

    def _llm_synthesize(
        self,
        keywords: str,
        materials: str,
        local_context: list[str],
    ) -> WebSearchInsight:
        """核心 LLM 调用：基于已格式化的材料字符串提炼行前洞察（失败返回空，由调用方降级）。"""
        config = self.client.config
        if not config.LLM_API_KEY or not materials:
            return WebSearchInsight()

        system_prompt = (
            "你是户外线路导览讲解员。只能基于用户提供的搜索材料与属地线索撰写，"
            "严禁捏造或使用材料之外的信息，没有可靠信息就写“未检索到可靠信息”。"
            "三条铁律：①用客观平实的陈述句讲解，像景区导览词或科普说明，"
            "禁止口语化、感叹、对话或煽情（不用“哦/啦/咱们/你”等口吻）；"
            "②禁止出现 POI、坐标、逆地理、GIS、瓦片等技术术语，地名机构直接用专名；"
            "③只保留与这条线路直接相关的地貌、景观、人文与攻略要点，无关内容一律丢弃，不要罗列来源。"
            "输出 JSON，不要 Markdown。"
        )
        user_prompt = (
            f"线路关键词：{keywords}\n"
            "请综合下方材料，客观讲解这条线路的沿途地貌、景观、人文与实用攻略要点，"
            "并单独列出应急电话；与线路无关的内容不要写进 summary。\n"
            "JSON 格式：{\"summary\":\"不超过220字的客观讲解\","
            "\"emergency_contacts\":[{\"name\":\"机构名\",\"phone\":\"电话\",\"contact_type\":\"医疗/救援/报警\"}]}\n"
            f"属地与周边线索：{'；'.join(local_context[:10]) or '无'}\n"
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
        """LLM 不可用时的本地降级摘要：尽量口语化，不带技术术语前缀。"""
        snippets: list[str] = []
        contacts: list[SearchEmergencyContact] = []
        seen_phones: set[str] = set()
        for response in responses:
            for result in response.results:
                text = " ".join(part for part in [result.title, result.content] if part)
                if text and len(snippets) < 3:
                    snippets.append(text[:80])
                for phone in self._extract_phone_numbers(text):
                    if phone in seen_phones:
                        continue
                    seen_phones.add(phone)
                    contacts.append(SearchEmergencyContact(
                        name=result.title[:40] or "网络检索电话",
                        phone=phone,
                        contact_type="救援",
                    ))
        parts: list[str] = []
        if local_context:
            parts.append("、".join(local_context[:4]))
        if snippets:
            parts.append("；".join(snippets))
        return WebSearchInsight(summary="；".join(parts), emergency_contacts=contacts[:6])

    def _format_search_materials(self, responses: List[WebSearchResponse]) -> str:
        """精简格式化搜索材料给 LLM：每条优先取摘要、控制条数与字数以压缩 token。"""
        lines: list[str] = []
        index = 1
        for response in responses:
            for result in response.results[:4]:
                text = result.content or result.raw_content or ""
                text = " ".join(text.split())[:400]
                if not text:
                    continue
                lines.append(f"{index}. {result.title}（{result.source}）：{text}")
                index += 1
                if index > 8:
                    return "\n".join(lines)
        return "\n".join(lines)

    @staticmethod
    def _format_references(references: List[WebReference]) -> str:
        """把前端回传的网络参考资料格式化为 LLM 材料字符串。"""
        lines: list[str] = []
        for i, ref in enumerate(references[:8], 1):
            text = " ".join((ref.snippet or "").split())[:400]
            if not text:
                continue
            lines.append(f"{i}. {ref.title}（{ref.source}）：{text}")
        return "\n".join(lines)

    @staticmethod
    def _clean_term(text: str) -> str:
        """清洗高德线索里的生硬技术标签，转成可读中文（local_context 进入 LLM/降级前调用）。"""
        if not text:
            return ""
        for old, new in (
            ("附近POI：", "附近有 "),
            ("周边POI：", "周边有 "),
            ("POI", "地点"),
            ("逆地理", "属地"),
        ):
            text = text.replace(old, new)
        return text.strip("：、， ")

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
