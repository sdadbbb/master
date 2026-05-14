import base64

# 替换成你的图片文件名
with open("OIP-C.jpg", "rb") as f:
    encoded_string = base64.b64encode(f.read()).decode('utf-8')
    print(encoded_string)
