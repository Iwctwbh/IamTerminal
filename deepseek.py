import subprocess
from openai import OpenAI
import locale
import os
import datetime
import time
import json

encoding = locale.getpreferredencoding()

client = OpenAI(api_key="lm-studio", base_url="http://10.11.12.18:1234/v1")

messages = [{"role": "system", "content": "用户会向你提需求，你需要完成用户的需求，用户侧有一个pwsh(powershell7)终端，你需要根据需求回复相应的代码和指令，每次执行命令都会回到当前执行环境的根目录，所以要时刻注意目录和文件位置，因为使用的是终端，应该注意引号嵌套的问题，还需要注意斜杠转译的问题，不需要markdown格式，不需要markdown格式，不需要markdown格式，你可以分步回复命令，一行一个命令，或者使用&&字符，除此之外你不需要其他额外的回复，用户会返回给你执行结果或者报错信息，否则用户会提出新的需求。"}]

# Create directory structure based on current date
current_time = datetime.datetime.now()
date_folder = current_time.strftime("%Y-%m-%d")
time_stamp = current_time.strftime("%H-%M-%S")
save_path = os.path.join("saves", date_folder)
os.makedirs(save_path, exist_ok=True)
conversation_file = os.path.join(save_path, f"conversation_{time_stamp}.json")

error_flag = False
user_input = ""
while True:
    if not error_flag:
        user_input = input("请输入您的需求：")
    else:
        error_flag = False
        input("发送错误信息，请按回车键继续：")
    messages.append({"role": "user", "content": user_input})
    print("等待回复中...")

    with open(conversation_file, "a", encoding="utf-8") as file:
        json.dump({"timestamp": current_time.strftime('%Y-%m-%d %H:%M:%S'), "role": "user", "content": user_input}, file)
        file.write("\n")

    start_time = time.time()
    response = client.chat.completions.create(
        model="qwen2.5-coder-32b-instruct",
        messages=messages,
        max_tokens=1024,
        temperature=0.7,
        stream=False
    )
    end_time = time.time()
    api_wait_time = end_time - start_time

    reply = response.choices[0].message.content
    print(reply)

    with open(conversation_file, "a", encoding="utf-8") as file:
        json.dump({"timestamp": current_time.strftime('%Y-%m-%d %H:%M:%S'), "role": "assistant", "content": reply, "api_wait_time": f"{api_wait_time:.2f} seconds"}, file)
        file.write("\n")

    messages.append({"role": "assistant", "content": reply})

    process = subprocess.Popen(["powershell", "-Command", f"{reply}"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=0)
    stdout, stderr = process.communicate(timeout=10)

    if stdout:
        print("PowerShell Output:\n", stdout.decode(encoding))
    if stderr:
        error_message = stderr.decode(encoding)
        print("PowerShell Error:\n", error_message)
        error_flag = True
        user_input = error_message