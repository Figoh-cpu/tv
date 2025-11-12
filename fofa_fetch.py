import os
import re
import requests
import time
import concurrent.futures
import subprocess

# ===============================
# 配置区
FOFA_URLS = {
    "https://fofa.info/result?qbase64=InVkcHh5IiAmJiBjb3VudHJ5PSJDTiI%3D": "ip.txt",
}
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

COUNTER_FILE = "计数.txt"
IP_DIR = "ip"
RTP_DIR = "rtp"
ZUBO_FILE = "zubo.txt"
IPTV_FILE = "tv.txt"

# ===============================
# 分类与映射配置
CHANNEL_CATEGORIES = {
    "央视频道": [
        "CCTV-1综合", "CCTV-2财经", "CCTV-3综艺", "CCTV-4中文国际", "CCTV-4欧洲", "CCTV-4美洲", "CCTV-5体育", "CCTV-5+体育赛事", "CCTV-6电影", "CCTV-7国防军事",
        "CCTV-8电视剧", "CCTV-9纪录", "CCTV-10科教", "CCTV-11戏曲", "CCTV-12社会与法", "CCTV-13新闻", "CCTV-14少儿", "CCTV-15音乐", "CCTV-16奥林匹克", "CCTV-17农业农村", "CCTV-4K", "CCTV-8K",
        "兵器科技", "风云音乐", "风云足球", "风云剧场", "怀旧剧场", "第一剧场", "女性时尚", "世界地理", "央视台球", "高尔夫·网球",
        "央视文化精品", "卫生健康", "电视指南"
    ],
    "卫视频道": [
        "湖南卫视", "浙江卫视", "江苏卫视", "东方卫视", "深圳卫视", "北京卫视", "广东卫视", "广西卫视", "东南卫视", "海南卫视",
        "河北卫视", "河南卫视", "湖北卫视", "江西卫视", "四川卫视", "重庆卫视", "贵州卫视", "云南卫视", "天津卫视", "安徽卫视",
        "山东卫视", "辽宁卫视", "黑龙江卫视", "吉林卫视", "内蒙古卫视", "宁夏卫视", "山西卫视", "陕西卫视", "甘肃卫视", "青海卫视",
        "新疆卫视", "西藏卫视", "三沙卫视", "兵团卫视", "延边卫视", "安多卫视", "康巴卫视", "农林卫视", "山东教育卫视",
        "中国教育1台", "中国教育2台", "中国教育3台", "中国教育4台", "早期教育"
    ],
    "国际频道": [
        "星空卫视", "CHANNEL[V]", "凤凰中文", "凤凰资讯", "凤凰香港", "凤凰电影"
    ],
    "数字频道": [
        "CHC动作电影", "CHC家庭影院", "CHC影迷电影", "北京IPTV淘电影", "北京IPTV淘精彩", "北京IPTV淘剧场", "北京IPTV淘4K", "北京IPTV淘娱乐", "北京IPTV淘BABY", "北京IPTV淘萌宠", "重温经典", "求索纪录", "求索科学",
        "求索生活", "求索动物", "纪实人文", "金鹰纪实", "纪实科教", "睛彩青少", "睛彩竞技", "睛彩篮球", "睛彩广场舞", "魅力足球", "五星体育",
        "劲爆体育", "快乐垂钓", "茶频道", "先锋乒羽", "天元围棋", "汽摩", "梨园频道", "文物宝库", "武术世界", "哒啵赛事", "哒啵电竞", "黑莓电影", "黑莓动画", 
        "乐游", "生活时尚", "都市剧场", "欢笑剧场", "游戏风云", "金色学堂", "动漫秀场", "新动漫", "卡酷少儿", "金鹰卡通", "优漫卡通", "哈哈炫动", "嘉佳卡通", 
        "中国交通", "中国天气", "华数4K", "华数星影", "华数动作影院", "华数喜剧影院", "华数家庭影院", "华数经典电影", "华数热播剧场", "华数碟战剧场",
        "华数军旅剧场", "华数城市剧场", "华数武侠剧场", "华数古装剧场", "华数魅力时尚", "华数少儿动画", "华数动画", "iHOT爱喜剧", "iHOT爱科幻", 
        "iHOT爱院线", "iHOT爱悬疑", "iHOT爱历史", "iHOT爱谍战", "iHOT爱旅行", "iHOT爱幼教", "iHOT爱玩具", "iHOT爱体育", "iHOT爱赛车", "iHOT爱浪漫", 
        "iHOT爱奇谈", "iHOT爱科学", "iHOT爱动漫",
    ],
    "山东频道": [
        "山东齐鲁", "山东新闻", "山东体育", "山东生活", "山东文旅", "山东综艺", "山东农科", "邹平综合", "滨州综合", "滨州民生", "沾化综合", "无棣综合",
        "惠民综合", "东营新闻", "淄博新闻", "淄博文旅", "淄博民生", "淄博影视", "淄川新闻", "张店综合", "周村新闻", "高青综合", "章丘综合", "临沂综合",
    ]
}

# ===== 映射（别名 -> 标准名） =====
CHANNEL_MAPPING = {
    "CCTV-1综合": ["CCTV-1", "CCTV-1 HD", "CCTV1 HD", "CCTV1"],
    "CCTV-2财经": ["CCTV-2", "CCTV-2 HD", "CCTV2 HD", "CCTV2"],
    "CCTV-3综艺": ["CCTV-3", "CCTV-3 HD", "CCTV3 HD", "CCTV3"],
    "CCTV-4中文国际": ["CCTV-4", "CCTV-4 HD", "CCTV4 HD", "CCTV4"],
    "CCTV-4欧洲": ["CCTV4欧洲", "CCTV-4欧洲", "CCTV4欧洲 HD", "CCTV-4 欧洲", "CCTV-4中文国际欧洲", "CCTV4中文欧洲"],
    "CCTV-4美洲": ["CCTV4美洲", "CCTV-4北美", "CCTV4美洲 HD", "CCTV-4 美洲", "CCTV-4中文国际美洲", "CCTV4中文美洲"],
    "CCTV-5体育": ["CCTV-5", "CCTV-5 HD", "CCTV5 HD", "CCTV5"],
    "CCTV-5+体育赛事": ["CCTV-5+", "CCTV-5+ HD", "CCTV5+ HD", "CCTV5+"],
    "CCTV-6电影": ["CCTV-6", "CCTV-6 HD", "CCTV6 HD", "CCTV6"],
    "CCTV-7国防军事": ["CCTV-7", "CCTV-7 HD", "CCTV7 HD", "CCTV7"],
    "CCTV-8电视剧": ["CCTV-8", "CCTV-8 HD", "CCTV8 HD", "CCTV8"],
    "CCTV-9纪录": ["CCTV-9", "CCTV-9 HD", "CCTV9 HD", "CCTV9"],
    "CCTV-10科教": ["CCTV-10", "CCTV-10 HD", "CCTV10 HD", "CCTV10"],
    "CCTV-11戏曲": ["CCTV-11", "CCTV-11 HD", "CCTV11 HD", "CCTV11"],
    "CCTV-12社会与法": ["CCTV-12", "CCTV-12 HD", "CCTV12 HD", "CCTV12"],
    "CCTV-13新闻": ["CCTV-13", "CCTV-13 HD", "CCTV13 HD", "CCTV13"],
    "CCTV-14少儿": ["CCTV-14", "CCTV-14 HD", "CCTV14 HD", "CCTV14"],
    "CCTV-15音乐": ["CCTV-15", "CCTV-15 HD", "CCTV15 HD", "CCTV15"],
    "CCTV-16奥林匹克": ["CCTV-16", "CCTV-16 HD", "CCTV-16 4K", "CCTV16", "CCTV16 4K", "CCTV-16奥林匹克4K"],
    "CCTV-17农业农村": ["CCTV-17", "CCTV-17 HD", "CCTV17 HD", "CCTV17"],
    "CCTV-4K": ["CCTV4K超高清", "CCTV4K", "CCTV-4K 超高清", "CCTV 4K"],
    "CCTV-8K": ["CCTV8K超高清", "CCTV8K", "CCTV-8K 超高清", "CCTV 8K"],
    "兵器科技": ["CCTV-兵器科技", "CCTV兵器科技"],
    "风云音乐": ["CCTV-风云音乐", "CCTV风云音乐"],
    "第一剧场": ["CCTV-第一剧场", "CCTV第一剧场"],
    "风云足球": ["CCTV-风云足球", "CCTV风云足球"],
    "风云剧场": ["CCTV-风云剧场", "CCTV风云剧场"],
    "怀旧剧场": ["CCTV-怀旧剧场", "CCTV怀旧剧场"],
    "女性时尚": ["CCTV-女性时尚", "CCTV女性时尚"],
    "世界地理": ["CCTV-世界地理", "CCTV世界地理"],
    "央视台球": ["CCTV-央视台球", "CCTV央视台球"],
    "高尔夫·网球": ["CCTV-高尔夫网球", "CCTV高尔夫网球", "CCTV央视高网", "CCTV-高尔夫·网球", "央视高网"],
    "央视文化精品": ["CCTV-央视文化精品", "CCTV央视文化精品", "CCTV文化精品", "CCTV-文化精品", "文化精品"],
    "卫生健康": ["CCTV-卫生健康", "CCTV卫生健康","卫生健康HD"],
    "电视指南": ["CCTV-电视指南", "CCTV电视指南"],
    "农林卫视": ["陕西农林卫视"],
    "三沙卫视": ["海南三沙卫视"],
    "兵团卫视": ["新疆兵团卫视"],
    "延边卫视": ["吉林延边卫视"],
    "安多卫视": ["青海安多卫视"],
    "康巴卫视": ["四川康巴卫视"],
    "山东教育卫视": ["山东教育", "山东教育卫视 576"],
    "中国教育1台": ["CETV1", "中国教育一台", "中国教育1", "CETV-1 综合教育", "CETV-1"],
    "中国教育2台": ["CETV2", "中国教育二台", "中国教育2", "CETV-2 空中课堂", "CETV-2"],
    "中国教育3台": ["CETV3", "中国教育三台", "中国教育3", "CETV-3 教育服务", "CETV-3"],
    "中国教育4台": ["CETV4", "中国教育四台", "中国教育4", "CETV-4 职业教育", "CETV-4"],
    "早期教育": ["中国教育5台", "中国教育5", "中国教育五台", "CETV早期教育", "华电早期教育", "CETV 早期教育", "CETV-5", "CETV5"],
    "湖南卫视": ["湖南卫视4K"],
    "北京卫视": ["北京卫视4K"],
    "东方卫视": ["东方卫视4K"],
    "广东卫视": ["广东卫视4K"],
    "深圳卫视": ["深圳卫视4K"],
    "山东卫视": ["山东卫视4K"],
    "四川卫视": ["四川卫视4K"],
    "浙江卫视": ["浙江卫视4K"],
    "CHC影迷电影": ["CHC高清电影", "CHC-影迷电影", "影迷电影", "chc高清电影"],
    "北京IPTV淘电影": ["IPTV淘电影", "淘电影", "北京淘电影"],
    "北京IPTV淘精彩": ["IPTV淘精彩", "淘精彩", "北京淘精彩"],
    "北京IPTV淘剧场": ["IPTV淘剧场", "淘剧场", "北京淘剧场"],
    "北京IPTV淘4K": ["IPTV淘4K", "北京IPTV4K超清", "北京淘4K", "淘4K", "淘 4K"],
    "北京IPTV淘娱乐": ["IPTV淘娱乐", "淘娱乐", "北京淘娱乐"],
    "北京IPTV淘BABY": ["IPTV淘BABY", "淘BABY", "北京淘BABY", "IPTV淘baby", "北京IPTV淘baby", "北京淘baby"],
    "北京IPTV淘萌宠": ["IPTV淘萌宠", "北京IPTV萌宠TV", "北京淘萌宠","淘萌宠"],
    "魅力足球": ["上海魅力足球"],
    "睛彩青少": ["睛彩羽毛球"],
    "求索纪录": ["求索记录", "求索纪录4K", "求索记录4K", "求索纪录 4K", "求索记录 4K"],
    "金鹰纪实": ["湖南金鹰纪实", "金鹰记实"],
    "纪实科教": ["北京纪实科教", "BRTV纪实科教", "纪实科教8K"],
    "星空卫视": ["星空衛視", "星空衛视", "星空卫視"],
    "CHANNEL[V]": ["CHANNEL-V", "Channel[V]"],
    "凤凰中文": ["凤凰中文", "凤凰中文台", "凤凰卫视中文", "凤凰卫视"],
    "凤凰香港": ["凤凰香港台", "凤凰卫视香港", "凤凰香港"],
    "凤凰资讯": ["凤凰资讯", "凤凰资讯台", "凤凰咨询", "凤凰咨询台", "凤凰卫视咨询台", "凤凰卫视资讯", "凤凰卫视咨询"],
    "凤凰电影": ["凤凰电影", "凤凰电影台", "凤凰卫视电影", "鳳凰衛視電影台", " 凤凰电影"],
    "茶频道": ["湖南茶频道"],
    "快乐垂钓": ["湖南快乐垂钓"],
    "先锋乒羽": ["湖南先锋乒羽"],
    "天元围棋": ["天元围棋频道"],
    "汽摩": ["重庆汽摩", "汽摩频道", "重庆汽摩频道"],
    "梨园频道": ["河南梨园频道", "梨园", "河南梨园"],
    "文物宝库": ["河南文物宝库"],
    "武术世界": ["河南武术世界"],
    "乐游": ["乐游频道", "上海乐游频道", "乐游纪实", "SiTV乐游频道", "SiTV 乐游频道"],
    "欢笑剧场": ["上海欢笑剧场4K", "欢笑剧场 4K", "欢笑剧场4K", "上海欢笑剧场"],
    "生活时尚": ["生活时尚4K", "SiTV生活时尚", "上海生活时尚"],
    "都市剧场": ["都市剧场4K", "SiTV都市剧场", "上海都市剧场"],
    "游戏风云": ["游戏风云4K", "SiTV游戏风云", "上海游戏风云"],
    "金色学堂": ["金色学堂4K", "SiTV金色学堂", "上海金色学堂"],
    "动漫秀场": ["动漫秀场4K", "SiTV动漫秀场", "上海动漫秀场"],
    "卡酷少儿": ["北京KAKU少儿", "BRTV卡酷少儿", "北京卡酷少儿", "卡酷动画"],
    "哈哈炫动": ["炫动卡通", "上海哈哈炫动"],
    "优漫卡通": ["江苏优漫卡通", "优漫漫画"],
    "金鹰卡通": ["湖南金鹰卡通"],
    "中国交通": ["中国交通频道"],
    "中国天气": ["中国天气频道"],
    "华数4K": ["华数低于4K", "华数4K电影", "华数爱上4K"],
    "iHOT爱喜剧": ["iHOT 爱喜剧", "IHOT 爱喜剧", "IHOT爱喜剧", "ihot爱喜剧", "爱喜剧", "ihot 爱喜剧"],
    "iHOT爱科幻": ["iHOT 爱科幻", "IHOT 爱科幻", "IHOT爱科幻", "ihot爱科幻", "爱科幻", "ihot 爱科幻"],
    "iHOT爱院线": ["iHOT 爱院线", "IHOT 爱院线", "IHOT爱院线", "ihot爱院线", "ihot 爱院线", "爱院线"],
    "iHOT爱悬疑": ["iHOT 爱悬疑", "IHOT 爱悬疑", "IHOT爱悬疑", "ihot爱悬疑", "ihot 爱悬疑", "爱悬疑"],
    "iHOT爱历史": ["iHOT 爱历史", "IHOT 爱历史", "IHOT爱历史", "ihot爱历史", "ihot 爱历史", "爱历史"],
    "iHOT爱谍战": ["iHOT 爱谍战", "IHOT 爱谍战", "IHOT爱谍战", "ihot爱谍战", "ihot 爱谍战", "爱谍战"],
    "iHOT爱旅行": ["iHOT 爱旅行", "IHOT 爱旅行", "IHOT爱旅行", "ihot爱旅行", "ihot 爱旅行", "爱旅行"],
    "iHOT爱幼教": ["iHOT 爱幼教", "IHOT 爱幼教", "IHOT爱幼教", "ihot爱幼教", "ihot 爱幼教", "爱幼教"],
    "iHOT爱玩具": ["iHOT 爱玩具", "IHOT 爱玩具", "IHOT爱玩具", "ihot爱玩具", "ihot 爱玩具", "爱玩具"],
    "iHOT爱体育": ["iHOT 爱体育", "IHOT 爱体育", "IHOT爱体育", "ihot爱体育", "ihot 爱体育", "爱体育"],
    "iHOT爱赛车": ["iHOT 爱赛车", "IHOT 爱赛车", "IHOT爱赛车", "ihot爱赛车", "ihot 爱赛车", "爱赛车"],
    "iHOT爱浪漫": ["iHOT 爱浪漫", "IHOT 爱浪漫", "IHOT爱浪漫", "ihot爱浪漫", "ihot 爱浪漫", "爱浪漫"],
    "iHOT爱奇谈": ["iHOT 爱奇谈", "IHOT 爱奇谈", "IHOT爱奇谈", "ihot爱奇谈", "ihot 爱奇谈", "爱奇谈"],
    "iHOT爱科学": ["iHOT 爱科学", "IHOT 爱科学", "IHOT爱科学", "ihot爱科学", "ihot 爱科学", "爱科学"],
    "iHOT爱动漫": ["iHOT 爱动漫", "IHOT 爱动漫", "IHOT爱动漫", "ihot爱动漫", "ihot 爱动漫", "爱动漫"],
    "山东齐鲁":["山东齐鲁频道", "sdql", "shandongqilu", "shandongql"],
    "山东新闻":["山东新闻频道", "sdxw", "shandongxinwen", "shandongxw"],
    "山东体育":["山东体育频道", "sdty", "shandongtiyu", "shandongty"],
    "山东生活":["山东生活频道", "sdsh", "shandongshenghuo", "shandongshenghuo"],
    "山东文旅":["山东文旅频道", "sdwl", "shandongwenlv", "shandongwenlv"],
    "山东综艺":["山东综艺频道", "sdzy", "shandongzongyi", "shandongzy"],
    "山东农科":["山东农科频道", "sdnk", "shandongnongke", "shandongnongke"],
    "邹平综合":["邹平综合频道", "zpzh", "zoupingzonghe", "zoupingzh"],
    "滨州综合":["滨州综合频道", "bzzh", "binzhouzonghe", "binzhouzh"],
    "滨州民生":["滨州民生频道", "bzsm", "binzhouminsheng", "binzhousm"],
    "沾化综合":["沾化综合频道", "zhzh", "zhanhuazonghe", "zhanhuazh"],
    "无棣综合":["无棣综合频道", "wdzh", "wudizonghe", "wudizonghe"],
    "惠民综合":["惠民综合频道", "hmzh", "huiminzonghe", "huiminzh"],
    "东营新闻":["东营新闻频道", "dyxw", "dongyingxinwen", "dongyingxw"],
    "淄博新闻":["淄博新闻频道", "zbxw", "ziboxinwen", "ziboxinwen"],
    "淄博文旅":["淄博文旅频道", "zbwl", "zibowenlv", "zibowenlv"],
    "淄博民生":["淄博民生频道", "zbsm", "zibominsheng", "zibosm"],
    "淄博影视":["淄博影视频道", "zbys", "ziboyingshi", "ziboyingshi"],
    "淄川新闻":["淄川新闻频道", "zcxw", "zichuanxinwen", "zichuanxw"],
    "张店综合":["张店综合频道", "zdzh", "zhangdianzonghe", "zhangdianzh"],
    "周村新闻":["周村新闻频道", "zcxxw", "zhoucunxinwen", "zhoucunxw"],
    "高青综合":["高青综合频道", "gqzh", "gaoqingzonghe", "gaoqingzh"],
    "章丘综合":["章丘综合频道", "zqzh", "zhangqiuzonghe", "zhangqiuzh"],
    "临沂综合":["临沂综合频道", "lyzh", "linyizonghe", "linyizh"],
}

# ===============================
# 计数逻辑
def get_run_count():
    if os.path.exists(COUNTER_FILE):
        try:
            return int(open(COUNTER_FILE).read().strip())
        except:
            return 0
    return 0

def save_run_count(count):
    open(COUNTER_FILE, "w").write(str(count))

def check_and_clear_files_by_run_count():
    os.makedirs(IP_DIR, exist_ok=True)
    count = get_run_count() + 1
    if count >= 73:
        print(f"🧹 第 {count} 次运行，清空 {IP_DIR} 下所有 .txt 文件")
        for f in os.listdir(IP_DIR):
            if f.endswith(".txt"):
                os.remove(os.path.join(IP_DIR, f))
        save_run_count(1)
        return "w", 1
    else:
        save_run_count(count)
        return "a", count

# ===============================
# IP 运营商判断
def get_isp(ip):
    if re.match(r"^(1[0-9]{2}|2[0-3]{2}|42|43|58|59|60|61|110|111|112|113|114|115|116|117|118|119|120|121|122|123|124|125|126|127|175|180|182|183|184|185|186|187|188|189|223)\.", ip):
        return "电信"
    elif re.match(r"^(42|43|58|59|60|61|110|111|112|113|114|115|116|117|118|119|120|121|122|123|124|125|126|127|175|180|182|183|184|185|186|187|188|189|223)\.", ip):
        return "联通"
    elif re.match(r"^(223|36|37|38|39|100|101|102|103|104|105|106|107|108|109|134|135|136|137|138|139|150|151|152|157|158|159|170|178|182|183|184|187|188|189)\.", ip):
        return "移动"
    else:
        return "未知"

# ===============================
# 第一阶段：爬取 + 分类写入
def first_stage():
    all_ips = set()
    for url, filename in FOFA_URLS.items():
        print(f"📡 正在爬取 {filename} ...")
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            urls_all = re.findall(r'<a href="http://(.*?)"', r.text)
            all_ips.update(u.strip() for u in urls_all)
        except Exception as e:
            print(f"❌ 爬取失败：{e}")
        time.sleep(3)

    province_isp_dict = {}
    for ip_port in all_ips:
        try:
            ip = ip_port.split(":")[0]
            res = requests.get(f"http://ip-api.com/json/{ip}?lang=zh-CN", timeout=10)
            data = res.json()
            province = data.get("regionName", "未知")
            isp = get_isp(ip)
            if isp == "未知":
                continue
            fname = f"{province}{isp}.txt"
            province_isp_dict.setdefault(fname, set()).add(ip_port)
        except Exception:
            continue

    mode, run_count = check_and_clear_files_by_run_count()
    for filename, ip_set in province_isp_dict.items():
        path = os.path.join(IP_DIR, filename)
        with open(path, mode, encoding="utf-8") as f:
            for ip_port in sorted(ip_set):
                f.write(ip_port + "\n")
        print(f"{path} 已{'覆盖' if mode=='w' else '追加'}写入 {len(ip_set)} 个 IP")
    print(f"✅ 第一阶段完成，当前轮次：{run_count}")
    return run_count

# ===============================
# 第二阶段：生成 zubo.txt
def second_stage():
    print("🔔 第二阶段触发：生成 zubo.txt")
    combined_lines = []
    for ip_file in os.listdir(IP_DIR):
        if not ip_file.endswith(".txt"):
            continue
        ip_path = os.path.join(IP_DIR, ip_file)
        rtp_path = os.path.join(RTP_DIR, ip_file)
        if not os.path.exists(rtp_path):
            continue

        with open(ip_path, encoding="utf-8") as f1, open(rtp_path, encoding="utf-8") as f2:
            ip_lines = [x.strip() for x in f1 if x.strip()]
            rtp_lines = [x.strip() for x in f2 if x.strip()]

        if not ip_lines or not rtp_lines:
            continue

        for ip_port in ip_lines:
            for rtp_line in rtp_lines:
                if "," not in rtp_line:
                    continue
                ch_name, rtp_url = rtp_line.split(",", 1)
                combined_lines.append(f"{ch_name},http://{ip_port}/rtp/{rtp_url.split('rtp://')[1]}")

    # 去重
    unique = {}
    for line in combined_lines:
        url_part = line.split(",", 1)[1]
        if url_part not in unique:
            unique[url_part] = line

    with open(ZUBO_FILE, "w", encoding="utf-8") as f:
        for line in unique.values():
            f.write(line + "\n")
    print(f"🎯 第二阶段完成，共 {len(unique)} 条有效 URL")

# ===============================
# 第三阶段：检测代表频道并生成 tv.txt（使用 ffprobe + 映射匹配 + 分类排序 + 多线程 + 后缀编号）
def third_stage():
    print("🧩 第三阶段：多线程检测代表频道生成 tv.txt")

    if not os.path.exists(ZUBO_FILE):
        print("⚠️ zubo.txt 不存在，跳过")
        return

    # ---- ffprobe 检测函数 ----
    def check_stream(url, timeout=5):
        try:
            result = subprocess.run(
                ["ffprobe", "-v", "error", "-show_streams", "-i", url],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=timeout + 2
            )
            return b"codec_type" in result.stdout
        except Exception:
            return False

    # ---- 建立别名反查表 ----
    alias_map = {}
    for main_name, aliases in CHANNEL_MAPPING.items():
        for alias in aliases:
            alias_map[alias] = main_name

    # ---- 读取 IP → 省份运营商 ----
    ip_info = {}
    for fname in os.listdir(IP_DIR):
        if not fname.endswith(".txt"):
            continue
        province_operator = fname.replace(".txt", "")
        path = os.path.join(IP_DIR, fname)
        with open(path, encoding="utf-8") as f:
            for line in f:
                ip_port = line.strip()
                ip_info[ip_port] = province_operator

    # ---- 从 zubo.txt 分组 ----
    groups = {}
    with open(ZUBO_FILE, encoding="utf-8") as f:
        for line in f:
            if "," not in line:
                continue
            ch_name, url = line.strip().split(",", 1)
            ch_main = alias_map.get(ch_name, ch_name)
            m = re.match(r"http://(\d+\.\d+\.\d+\.\d+:\d+)/", url)
            if m:
                ip_port = m.group(1)
                groups.setdefault(ip_port, []).append((ch_main, url))

    # ---- 多线程检测每个 IP 是否可播放 ----
    def detect_ip(ip_port, entries):
        rep_channels = [u for c, u in entries if c == "CCTV1"]
        if not rep_channels and entries:
            rep_channels = [entries[0][1]]
        playable = any(check_stream(u) for u in rep_channels)
        return ip_port, playable

    print(f"🚀 启动多线程检测（共 {len(groups)} 个 IP）...")
    playable_ips = set()
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(detect_ip, ip, chs): ip for ip, chs in groups.items()}
        for future in concurrent.futures.as_completed(futures):
            ip_port, ok = future.result()
            if ok:
                playable_ips.add(ip_port)

    print(f"✅ 检测完成，可播放 IP 共 {len(playable_ips)} 个")

    # ---- 生成最终去重 IPTV 列表 ----
    valid_lines = []
    seen = set()

    for ip_port in playable_ips:
        province_operator = ip_info.get(ip_port, "未知")
        for c, u in groups[ip_port]:
            key = f"{c},{u}"
            if key not in seen:
                seen.add(key)
                valid_lines.append(f"{c},{u}${province_operator}")

    # ---- 分类写出 tv.txt ----
    with open(IPTV_FILE, "w", encoding="utf-8") as f:
        for category, ch_list in CHANNEL_CATEGORIES.items():
            f.write(f"{category},#genre#\n")
            for ch in ch_list:
                for line in valid_lines:
                    name = line.split(",", 1)[0]
                    if name == ch:
                        f.write(line + "\n")
            f.write("\n")

    print(f"🎯 tv.txt 生成完成（分类+去重+多线程检测），共 {len(valid_lines)} 条频道")

# ===============================
# 文件推送（⚠️ 已去掉 zubo.txt）
def push_all_files():
    print("🚀 推送所有更新文件到 GitHub...")
    os.system('git config --global user.name "github-actions"')
    os.system('git config --global user.email "github-actions@users.noreply.github.com"')
    os.system("git add 计数.txt")
    os.system("git add ip/*.txt || true")
    os.system("git add tv.txt || true")
    os.system('git commit -m "自动更新：计数、IP文件、tv.txt" || echo "⚠️ 无需提交"')
    os.system("git push origin main || echo '⚠️ 推送失败'")


# ===============================
# 主执行逻辑
if __name__ == "__main__":
    run_count = first_stage()
    if run_count in [12, 24, 36, 48, 60, 72]:
        second_stage()
        third_stage()
    push_all_files()
