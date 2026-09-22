这是我的个人AI学习助手，会随着我AI能力的提升而不断升级<br>

设计流程：

V0.1  AI聊天助手 
      ↓<br>  
V0.2  具有个人记忆的助手 
      ↓<br>  
V0.3  AI知识库助手（RAG）  
      ↓<br>
V0.4  AI代码助手（Tool Use）
      ↓<br>
V0.5  Agent智能助手
      ↓<br>
V1.0  个人AI第二大脑


代码结构：

config->读取Deepseek api_key <br>
llm->选择Deepseek模型 <br>
prompt->个性化提示词 <br>
memory->管理对话记忆 <br>
long_term_memory->利用Deepseek总结长期记忆 <br>
main->程序执行入口 <br>
