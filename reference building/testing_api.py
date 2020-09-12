import requests

url = 'http://localhost:5000'
req = requests.delete(url + '/api/1')
# {
#     'title' : "my sec test",
#     'content' : 'uttam bvc'
# })

print(req.text)