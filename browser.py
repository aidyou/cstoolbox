import asyncio
import os

from langchain_openai import ChatOpenAI
from browser_use import Agent
from pydantic import SecretStr
from browser_use import BrowserConfig, Browser


async def main():
    browser_config = BrowserConfig(
        # headless=True,
        disable_security=True,
        # chrome_instance_path="/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
    )
    browser = Browser(config=browser_config)
    api_key = SecretStr(os.getenv("TEST_AI_API_KEY"))
    # 创建 AI 代理
    agent = Agent(
        task="帮我搜索下 deepseek-v3，看哪家云服务商最便宜且稳定",
        llm=ChatOpenAI(
            base_url=os.getenv("TEST_AI_URL"),
            # model="Qwen/Qwen2.5-7B-Instruct",
            model="Qwen/QwQ-32B",
            # model="Pro/deepseek-ai/DeepSeek-V3",
            api_key=api_key,
        ),
        use_vision=False,
        save_conversation_path="./logs/conversation",
        browser=browser,
    )
    # 执行任务
    result = await agent.run()
    print(f"任务结果: {result.final_result()}")


if __name__ == "__main__":
    asyncio.run(main())
