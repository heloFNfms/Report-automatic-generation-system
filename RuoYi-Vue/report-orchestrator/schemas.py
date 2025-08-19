from pydantic import BaseModel
from typing import List, Dict, Optional

class Step1Req(BaseModel):
    项目标题: str
    公司名称: str
    研究内容: str

class Step2Req(BaseModel):
    项目标题: str
    研究内容: str

class Step2Resp(BaseModel):
    摘要: str
    关键词: List[str]
    参考网址: List[str]

class Step3Req(BaseModel):
    摘要: str
    关键词: List[str]

class OutlineItem(BaseModel):
    一级标题: str
    二级标题: List[str]

class Step3Resp(BaseModel):
    研究大纲: List[OutlineItem]
    参考网址: List[str]

class Step4Req(BaseModel):
    研究大纲: List[OutlineItem]

class Step4Resp(BaseModel):
    研究内容: Dict[str, Dict[str, str]]
    参考网址: List[str]

class Step5Req(BaseModel):
    摘要: str
    关键词: List[str]
    研究大纲: List[OutlineItem]
    研究内容: Dict[str, Dict[str, str]]

class Step5Resp(BaseModel):
    标题: str
    摘要: str
    关键词: List[str]
    正文: str
    参考文献: List[str]
