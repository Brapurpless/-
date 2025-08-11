import requests
import logging
import os
from volcenginesdkarkruntime import Ark

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AIAPI:
    def __init__(self):
        self.model_name = "doubao-1-5-pro-32k-250115"
        
        # 从环境变量中读取API密钥
        self.api_key = os.environ.get("ARK_API_KEY")
        if not self.api_key:
            raise ValueError("ARK_API_KEY环境变量未设置")
        
        # 初始化Ark客户端
        self.client = Ark(
            base_url="https://ark.cn-beijing.volces.com/api/v3",
            api_key=self.api_key
        )

    def generate_lesson_plan(self, prompt):
        for retry in range(3):
            try:
                logger.info(f"正在调用AI API生成教案，提示词: {prompt}")
                
                completion = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": "你是人工智能助手."},
                        {"role": "user", "content": prompt}
                    ]
                )
                
                logger.info("AI API调用成功")
                return {
                    "status": "success",
                    "result": completion.choices[0].message.content
                }
                
            except Exception as e:
                logger.error(f"API调用错误: {str(e)}")
                if retry == 2:
                    return {
                        "status": "error",
                        "message": f"API调用错误: {str(e)}"
                    }

    def ask_question(self, question, user_role):
        """
        处理来自用户的通用问题
        :param question: 用户的问题
        :param user_role: 用户角色（学校、教师、家长）
        :return: 包含状态和结果的字典
        """
        for retry in range(3):
            try:
                logger.info(f"正在调用AI API回答{user_role}的问题，问题: {question}")
                
                # 根据用户角色设置不同的系统提示
                system_prompt = "你是人工智能助手，"
                if user_role == "学校":
                    system_prompt += "擅长回答学校管理者关于教育政策、学校管理等方面的问题。"
                elif user_role == "教师":
                    system_prompt += "擅长回答教师关于教学设计、教学方法、学科知识等方面的问题。"
                elif user_role == "家长":
                    system_prompt += "擅长回答家长关于孩子教育、亲子沟通、家庭教育等方面的问题。"
                
                completion = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": question}
                    ]
                )
                
                logger.info("AI API调用成功")
                return {
                    "status": "success",
                    "result": completion.choices[0].message.content
                }
                
            except Exception as e:
                logger.error(f"API调用错误: {str(e)}")
                if retry == 2:
                    return {
                        "status": "error",
                        "message": f"API调用错误: {str(e)}"
                    }