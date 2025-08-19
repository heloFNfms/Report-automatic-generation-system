import requests
BASE = 'http://localhost:9000'
# create task
r = requests.post(BASE + '/step1', json={"project_name":"AR target recognition","company_name":"ACME","research_content":"RAG + MCP + LangChain report generator"})
print(r.json())
TASK_ID = r.json().get('task_id')
# step2
r = requests.post(BASE + '/step2', json={"task_id":TASK_ID})
print(r.json())