import socket, sys

HOST, PORT = 'localhost', 8080

def create_msg(msg):
    return bytes(msg + '\n', 'utf-8')

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((HOST, PORT))
#message += create_msg(r"curl --header 'Host: mirror.internode.on.net' --header 'User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:36.0) Gecko/20100101 Firefox/36.0' --header 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8' --header 'Accept-Language: en-US,en;q=0.5' --header 'DNT: 1' --header 'Referer: http://mirror.internode.on.net/pub/test/' --header 'Cookie: _ga=GA1.3.335978841.1426489996; __utma=1.335978841.1426489996.1426489996.1426489996.1; __utmb=1.2.10.1426489996; __utmc=1; __utmz=1.1426489996.1.1.utmcsr=google|utmccn=(organic)|utmcmd=organic|utmctr=(not%20provided); _dc_gtm_UA-9015291-2=1; __utmt=1' --header 'Connection: keep-alive' 'http://mirror.internode.on.net/pub/test/10meg.test' -o '10meg.test' -L")
#message += create_msg(r'download http://mirror.internode.on.net/pub/test/1meg.test 1meg.test')
message = create_msg(r"curl --header 'Host: lx.cdn.baidupcs.com' --header 'User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:36.0) Gecko/20100101 Firefox/36.0' --header 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8' --header 'Accept-Language: en-US,en;q=0.5' --header 'DNT: 1' --header 'Referer: http://pan.baidu.com/share/link?shareid=2487404008&uk=1714331122' --header 'Connection: keep-alive' 'http://lx.cdn.baidupcs.com/file/f9af7e7f7cc6b01e2414393512ae6432?bkt=p2-nb-633&xcode=73f154b857d20b2211a4750111ff762bc81b5296ca64b013ed03e924080ece4b&fid=1714331122-250528-838788308783035&time=1426576042&sign=FDTAXERLBH-DCb740ccc5511e5e8fedcff06b081203-Jt8AfSsBtSdSI96B5SXhaL0wJMg%3D&to=cb&fm=Nin,B,U,ny&sta_dx=98&sta_cs=12&sta_ft=rar&sta_ct=0&newver=1&newfm=1&flow_ver=3&sl=80347212&expires=8h&rt=sh&r=652117419&mlogid=3737172623&vuk=489241497&vbdid=3042130563&fin=%E5%B8%95%E7%A7%8B%E8%8E%89%E5%A4%A7%E4%BA%BA%E7%9A%84%E5%8F%AC%E5%94%A4%E6%9C%AF%E8%AF%BE%E7%A8%8B%20v1.03.rar&fn=%E5%B8%95%E7%A7%8B%E8%8E%89%E5%A4%A7%E4%BA%BA%E7%9A%84%E5%8F%AC%E5%94%A4%E6%9C%AF%E8%AF%BE%E7%A8%8B%20v1.03.rar' -o '帕秋莉大人的召唤术课程 v1.03.rar' -L") 
message += create_msg('')
sock.sendall(message)


received_msg = sock.recv(2048)
print(received_msg)
sock.close()
