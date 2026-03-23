"""
LLM API 测试
============

测试硅基流动（Silicon Flow）大模型 API 调用。
"""

import json
import pytest
import requests
from pathlib import Path
import sys

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.api.config import api_config  # noqa: E402


class TestLLMAPI:
    """LLM API 测试类"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """测试前检查 API Key"""
        self.api_key = api_config.LLM_API_KEY
        self.base_url = api_config.LLM_BASE_URL
        self.proxy = api_config.PROXY if api_config.should_use_proxy() else None

        if not self.api_key:
            pytest.skip("未配置 LLM_API_KEY，跳过 LLM API 测试")

    @pytest.mark.llm
    def test_api_key_not_empty(self):
        """测试 API Key 不为空"""
        assert self.api_key, "LLM_API_KEY 不能为空"
        assert self.api_key != "your_llm_api_key_here", "请配置真实的 LLM_API_KEY"

    @pytest.mark.llm
    def test_simple_chat_completion(self):
        """测试简单的对话补全请求"""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        payload = {
            "model": "Pro/moonshotai/Kimi-K2.5",
            "messages": [
                {
                    "role": "user",
                    "content": "请用一句话回复：你好"
                }
            ],
            "temperature": 0.7,
            "max_tokens": 100
        }

        response = requests.post(
            self.base_url,
            headers=headers,
            json=payload,
            timeout=30,
            proxies=self.proxy
        )

        assert response.status_code == 200, f"API 返回错误: {response.status_code} - {response.text}"

        result = response.json()
        assert "choices" in result, f"响应格式错误，缺少 choices: {result}"
        assert len(result["choices"]) > 0, "choices 为空"

        content = result["choices"][0]["message"]["content"]
        assert content, "返回内容为空"
        print(f"\n[OK] LLM 回复: {content}")

    @pytest.mark.llm
    def test_json_response_format(self):
        """测试 JSON 格式响应"""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        payload = {
            "model": "Pro/moonshotai/Kimi-K2.5",
            "messages": [
                {
                    "role": "system",
                    "content": "你是一个助手，必须以 JSON 格式回复。"
                },
                {
                    "role": "user",
                    "content": "请返回一个简单的 JSON 对象，包含 name 和 age 两个字段，name 为 '测试', age 为 25"
                }
            ],
            "temperature": 0.1,
            "max_tokens": 200,
            "response_format": {"type": "json_object"}
        }

        response = requests.post(
            self.base_url,
            headers=headers,
            json=payload,
            timeout=30,
            proxies=self.proxy
        )

        assert response.status_code == 200, f"API 返回错误: {response.status_code} - {response.text}"

        result = response.json()
        content = result["choices"][0]["message"]["content"]

        # 验证返回内容是有效的 JSON
        try:
            # 清理可能的控制字符（LLM 有时会在 JSON 中包含换行符等）
            import re
            cleaned_content = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', content)
            # 清理多余的换行和空格
            cleaned_content = cleaned_content.strip()
            parsed = json.loads(cleaned_content)
            assert isinstance(parsed, dict), "返回的 JSON 不是对象"
            print(f"\n[OK] JSON 响应解析成功: {parsed}")
        except json.JSONDecodeError as e:
            pytest.fail(f"返回内容不是有效的 JSON: {content[:200]}, 错误: {e}")

    @pytest.mark.api
    @pytest.mark.llm
    def test_system_prompt_context(self):
        """测试系统提示词 + 用户上下文的请求模式"""
        from src.prompts import get_system_prompt

        system_prompt = get_system_prompt()

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        # 简化的用户提示词（模拟真实的规划请求）
        user_prompt = """
请根据以下户外活动规划信息，生成一个简单的户外活动计划：

## 用户原始请求
周末去香山徒步，预计10公里

## 轨迹分析信息
- 总距离：10.0公里
- 总爬升：500米
- 难度：中等

## 输出要求
请返回一个最小化的 JSON 对象，仅包含以下字段：
- plan_name: 计划名称
- overall_rating: 推荐等级（推荐|谨慎推荐|不推荐）
- track_overview: 轨迹概述
- weather_overview: 天气概述
- transport_overview: 交通概述
"""

        payload = {
            "model": "Pro/moonshotai/Kimi-K2.5",
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt[:2000]  # 截取部分以节省 token
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ],
            "temperature": 0.7,
            "max_tokens": 1000,
            "response_format": {"type": "json_object"}
        }

        response = requests.post(
            self.base_url,
            headers=headers,
            json=payload,
            timeout=60,
            proxies=self.proxy
        )

        assert response.status_code == 200, f"API 返回错误: {response.status_code} - {response.text}"

        result = response.json()
        content = result["choices"][0]["message"]["content"]

        # 验证返回内容是有效的 JSON
        try:
            # 清理可能的控制字符（LLM 有时会在 JSON 中包含换行符等）
            import re
            cleaned_content = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', content)
            # 清理多余的换行和空格
            cleaned_content = cleaned_content.strip()
            parsed = json.loads(cleaned_content)
            print("\n[OK] 规划 JSON 解析成功:")
            print(f"   - plan_name: {parsed.get('plan_name', 'N/A')}")
            print(f"   - overall_rating: {parsed.get('overall_rating', 'N/A')}")
            print(f"   - track_overview: {parsed.get('track_overview', 'N/A')}")
        except json.JSONDecodeError as e:
            pytest.fail(f"返回内容不是有效的 JSON: {content[:300]}, 错误: {e}")

    @pytest.mark.llm
    def test_available_models(self):
        """测试可用的模型列表"""
        # 硅基流动的模型列表端点
        models_url = "https://api.siliconflow.cn/v1/models"

        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }

        response = requests.get(
            models_url,
            headers=headers,
            timeout=30,
            proxies=self.proxy
        )

        if response.status_code == 200:
            result = response.json()
            models = result.get("data", [])
            print(f"\n[OK] 可用模型列表 ({len(models)} 个):")
            for model in models[:10]:  # 只显示前10个
                print(f"   - {model.get('id', 'unknown')}")
            if len(models) > 10:
                print(f"   ... 还有 {len(models) - 10} 个模型")
        else:
            print(f"\n[WARN] 获取模型列表失败: {response.status_code}")
            # 不作为测试失败，因为某些 API 可能不支持此端点


@pytest.mark.api
class TestLLMConnection:
    """LLM 连接测试（无需 API Key 的基础测试）"""

    def test_base_url_format(self):
        """测试 API 基础 URL 格式"""
        assert "siliconflow" in api_config.LLM_BASE_URL.lower(), \
            f"LLM_BASE_URL 应该指向硅基流动: {api_config.LLM_BASE_URL}"
        assert api_config.LLM_BASE_URL.startswith("https://"), \
            "LLM_BASE_URL 应该使用 HTTPS"

    def test_proxy_config(self):
        """测试代理配置"""
        if api_config.should_use_proxy():
            assert "http" in api_config.PROXY.get("http", ""), \
                "HTTP 代理配置无效"
            print(f"\n[OK] 使用代理: {api_config.PROXY}")
        else:
            print("\n[OK] 不使用代理")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "-m", "api"])
