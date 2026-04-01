#!/usr/bin/env python3
"""
upload_to_cloud.py — 投研鸭云数据库上传器 v1.1

v1.1 变更（2026-04-01）：
- 新增上传后回读校验模块 verify_upload()
  - 必填字段存在性校验（VERIFY_FIELDS）
  - 数组字段长度校验（ARRAY_LENGTH_RULES）
  - dataTime 一致性校验（防止字段截断）
- 上传主流程新增回读校验阶段（verify pass/fail 统计）
- 新增 uploaded_data 字典，记录成功上传的本地数据用于后续校验
将提取好的 JSON 数据通过微信云开发 HTTP API 上传到云数据库，
并在上传后自动回读校验关键字段完整性。

用法：
    python3 upload_to_cloud.py <JSON文件目录> <日期YYYY-MM-DD>

前提条件：
    1. 已在微信公众平台开通云开发
    2. 已创建4个数据库集合：briefing / markets / watchlist / radar
    3. 在本脚本中配置好 APPID / APPSECRET / CLOUD_ENV

配置方式（二选一）：
    方式1（推荐）：设置环境变量
        export WX_APPID="你的AppID"
        export WX_APPSECRET="你的AppSecret"
        export WX_CLOUD_ENV="你的云环境ID"

    方式2：直接修改下方 CONFIG 字典中的值
"""

import sys
import os
import json
import time

try:
    import requests
except ImportError:
    print("❌ 缺少 requests 库，请先安装：pip3 install requests")
    sys.exit(1)


# ═══════════════════════════════════════════════════════════════
# 配置（环境变量 > 硬编码值）
# ═══════════════════════════════════════════════════════════════

CONFIG = {
    # 你的小程序 AppID（在 project.config.json 或微信公众平台获取）
    'APPID': os.environ.get('WX_APPID', ''),
    # 你的小程序 AppSecret（在微信公众平台 → 开发管理 → 开发设置 中获取）
    'APPSECRET': os.environ.get('WX_APPSECRET', ''),
    # 你的云环境 ID（在微信开发者工具 → 云开发控制台 中查看）
    'CLOUD_ENV': os.environ.get('WX_CLOUD_ENV', ''),
}

# 需要上传的4个集合名称（与小程序中的数据库集合名一一对应）
COLLECTIONS = ['briefing', 'markets', 'watchlist', 'radar']

# ═══════════════════════════════════════════════════════════════
# v1.1 上传后回读校验配置
# ═══════════════════════════════════════════════════════════════

# 各集合必须存在且非空的关键字段
VERIFY_FIELDS = {
    "briefing":  [
        "date", "coreEvent", "globalReaction", "coreJudgments",
        "actions", "sentimentScore", "riskNote", "dataTime",
    ],
    "markets":   [
        "date", "usMarkets", "m7", "asiaMarkets",
        "commodities", "cryptos", "gics", "dataTime",
    ],
    "watchlist": ["date", "sectors", "stocks", "dataTime"],
    "radar":     [
        "date", "trafficLights", "riskScore", "riskLevel",
        "monitorTable", "riskAlerts", "events", "alerts",
        "smartMoneyDetail", "dataTime",
    ],
}

# 数组字段长度要求 (min_len, max_len)
ARRAY_LENGTH_RULES = {
    "briefing":  {
        "globalReaction": (5, 6),
        "coreJudgments":  (3, 3),
    },
    "markets":   {
        "usMarkets":   (4, 4),
        "m7":          (7, 7),
        "asiaMarkets": (4, 6),
        "commodities": (6, 6),
        "gics":        (11, 11),
    },
    "watchlist": {
        "sectors": (7, 7),
    },
    "radar":     {
        "trafficLights": (7, 7),
        "riskAlerts":    (2, 3),
        "events":        (3, 5),
    },
}

# access_token 缓存（避免重复请求，有效期2小时）
_token_cache = {
    'token': None,
    'expire_time': 0
}


# ═══════════════════════════════════════════════════════════════
# 微信 API 调用封装
# ═══════════════════════════════════════════════════════════════

def get_access_token():
    """
    获取微信 access_token（有2小时缓存）

    什么是 access_token？
    → 你可以把它理解为一把"临时钥匙"。每次我们要往微信云数据库写数据，
      都需要先拿到这把钥匙证明身份。钥匙每2小时过期，需要重新获取。
    """
    now = time.time()
    if _token_cache['token'] and now < _token_cache['expire_time']:
        return _token_cache['token']

    appid = CONFIG['APPID']
    secret = CONFIG['APPSECRET']

    if not appid or not secret:
        print("❌ 未配置 APPID 或 APPSECRET！")
        print("   请设置环境变量 WX_APPID 和 WX_APPSECRET")
        print("   或直接在脚本 CONFIG 中填写")
        return None

    url = (
        f"https://api.weixin.qq.com/cgi-bin/token"
        f"?grant_type=client_credential&appid={appid}&secret={secret}"
    )

    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        if 'access_token' in data:
            _token_cache['token'] = data['access_token']
            # 缓存时间设短一点（100分钟），留点余量
            _token_cache['expire_time'] = now + 6000
            print(f"   🔑 access_token 获取成功（有效期2小时）")
            return data['access_token']
        else:
            print(f"❌ 获取 access_token 失败: {data}")
            if data.get('errcode') == 40013:
                print("   → AppID 不正确，请检查配置")
            elif data.get('errcode') == 40125:
                print("   → AppSecret 不正确，请在微信公众平台重新获取")
            return None
    except Exception as e:
        print(f"❌ 网络请求失败: {e}")
        return None


def cloud_db_query(collection, date):
    """
    查询云数据库中是否已有当天的数据

    为什么要先查询？
    → 避免重复写入。如果你今天跑了两次日报，第二次应该"更新"而不是"新增"。
    """
    token = get_access_token()
    if not token:
        return None

    env = CONFIG['CLOUD_ENV']
    url = f"https://api.weixin.qq.com/tcb/databasequery?access_token={token}"

    query_str = f'db.collection("{collection}").where({{date: "{date}"}}).limit(1).get()'

    body = {
        "env": env,
        "query": query_str
    }

    try:
        resp = requests.post(url, json=body, timeout=15)
        result = resp.json()
        if result.get('errcode', 0) == 0:
            data_list = result.get('data', [])
            # data 是 JSON 字符串数组，需要解析
            if data_list:
                return json.loads(data_list[0])
            return None
        else:
            print(f"   ⚠️ 查询失败: {result}")
            return None
    except Exception as e:
        print(f"   ⚠️ 查询异常: {e}")
        return None


def _sanitize_for_query(obj):
    """
    递归清理数据中的特殊字符，避免微信云开发 query 解析失败。
    主要处理：
      - 换行符 → 空格（避免 Unterminated string literal）
      - 双引号 → 中文引号（避免破坏 query 字符串）
      - 反斜杠 → 正斜杠（避免转义混乱）
    """
    if isinstance(obj, str):
        s = obj
        # 先处理换行符（必须在反斜杠处理之前）
        s = s.replace('\r\n', ' ').replace('\n', ' ').replace('\r', ' ')
        # 再处理反斜杠和双引号
        s = s.replace('\\', '/').replace('"', '\\"')
        return s
    elif isinstance(obj, dict):
        return {k: _sanitize_for_query(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_sanitize_for_query(item) for item in obj]
    else:
        return obj


def cloud_db_add(collection, data):
    """
    向云数据库新增一条记录

    相当于：在一张Excel表格里新增一行数据
    """
    token = get_access_token()
    if not token:
        return False

    env = CONFIG['CLOUD_ENV']
    url = f"https://api.weixin.qq.com/tcb/databaseadd?access_token={token}"

    # 先清理特殊字符，再转为 JSON 字符串
    safe_data = _sanitize_for_query(data)
    data_str = json.dumps(safe_data, ensure_ascii=False)

    body = {
        "env": env,
        "query": f'db.collection("{collection}").add({{data: {data_str}}})'
    }

    try:
        resp = requests.post(url, json=body, timeout=15)
        result = resp.json()
        if result.get('errcode', 0) == 0:
            return True
        else:
            print(f"   ⚠️ 新增失败: {result}")
            return False
    except Exception as e:
        print(f"   ⚠️ 新增异常: {e}")
        return False


def cloud_db_update(collection, date, data):
    """
    更新云数据库中已有的记录

    相当于：在Excel表格中找到今天这一行，修改里面的数据
    """
    token = get_access_token()
    if not token:
        return False

    env = CONFIG['CLOUD_ENV']
    url = f"https://api.weixin.qq.com/tcb/databaseupdate?access_token={token}"

    # 构建 update 数据（排除 _id 和 date 字段）
    update_data = {k: v for k, v in data.items() if k not in ('_id', 'date')}
    safe_data = _sanitize_for_query(update_data)
    data_str = json.dumps(safe_data, ensure_ascii=False)

    body = {
        "env": env,
        "query": f'db.collection("{collection}").where({{date: "{date}"}}).update({{data: {data_str}}})'
    }

    try:
        resp = requests.post(url, json=body, timeout=15)
        result = resp.json()
        if result.get('errcode', 0) == 0:
            return True
        else:
            print(f"   ⚠️ 更新失败: {result}")
            return False
    except Exception as e:
        print(f"   ⚠️ 更新异常: {e}")
        return False


def upsert_data(collection, date, data):
    """
    智能写入：有则更新，无则新增（upsert模式）
    """
    data['date'] = date
    data['_updateTime'] = int(time.time() * 1000)  # 毫秒时间戳

    # 先查是否已有当天数据
    existing = cloud_db_query(collection, date)
    if existing:
        print(f"   📝 {collection}: 发现已有数据，执行更新...")
        return cloud_db_update(collection, date, data)
    else:
        print(f"   📝 {collection}: 无历史数据，执行新增...")
        return cloud_db_add(collection, data)


# ═══════════════════════════════════════════════════════════════
# v1.1 新增：上传后回读校验
# ═══════════════════════════════════════════════════════════════

def verify_upload(collection: str, date: str, local_data: dict) -> dict:
    """
    上传后回读云端数据，核验关键字段是否完整写入。

    检查项：
    1. 云端记录存在（回读成功）
    2. 所有必填字段非空（VERIFY_FIELDS）
    3. 数组字段长度在允许范围内（ARRAY_LENGTH_RULES）
    4. dataTime 字段与本地一致（防止写入时被截断）

    返回: {
        "ok": bool,
        "error": str (仅当回读失败时),
        "missing_fields": list,
        "array_errors": list,
        "dataTime_match": bool,
        "cloud_date": str,
    }
    """
    time.sleep(0.8)  # 等待云端写入完成，避免读写竞争

    cloud_record = cloud_db_query(collection, date)
    if not cloud_record:
        return {
            "ok": False,
            "error": "回读失败：云端无匹配记录（可能写入尚未完成，或集合名称不匹配）",
            "missing_fields": [],
            "array_errors": [],
            "dataTime_match": False,
            "cloud_date": "unknown",
        }

    missing_fields = []
    array_errors = []

    # 1. 必填字段存在性检查
    for field in VERIFY_FIELDS.get(collection, []):
        val = cloud_record.get(field)
        if val is None or val == "" or val == [] or val == {}:
            missing_fields.append(field)

    # 2. 数组长度校验
    for field, (min_len, max_len) in ARRAY_LENGTH_RULES.get(collection, {}).items():
        arr = cloud_record.get(field, [])
        actual_len = len(arr) if isinstance(arr, list) else 0
        if not (min_len <= actual_len <= max_len):
            array_errors.append(
                f"{field}: 期望{min_len}-{max_len}项，云端实际{actual_len}项"
            )

    # 3. dataTime 一致性（检测字段截断）
    local_dt = local_data.get("dataTime", "").strip()
    cloud_dt = cloud_record.get("dataTime", "").strip()
    dt_match = (local_dt == cloud_dt)

    ok = (len(missing_fields) == 0 and len(array_errors) == 0 and dt_match)

    return {
        "ok": ok,
        "missing_fields": missing_fields,
        "array_errors": array_errors,
        "dataTime_match": dt_match,
        "cloud_date": cloud_record.get("date", "unknown"),
    }


# ═══════════════════════════════════════════════════════════════
# 主流程
# ═══════════════════════════════════════════════════════════════

def main():
    if len(sys.argv) < 3:
        print("=" * 60)
        print("投研鸭 — 云数据库上传器 v1.1")
        print("=" * 60)
        print()
        print("用法: python3 upload_to_cloud.py <JSON目录> <日期>")
        print()
        print("示例:")
        print("  python3 upload_to_cloud.py ./output/ 2026-03-31")
        print()
        print("前提:")
        print("  1. 设置环境变量 WX_APPID / WX_APPSECRET / WX_CLOUD_ENV")
        print("  2. 微信云开发中已创建集合: briefing / markets / watchlist / radar")
        print()
        sys.exit(1)

    data_dir = sys.argv[1]
    date = sys.argv[2]

    print("=" * 60)
    print(f"🦆 投研鸭云数据库上传 — {date}")
    print("=" * 60)

    # 检查配置
    if not CONFIG['APPID'] or not CONFIG['APPSECRET'] or not CONFIG['CLOUD_ENV']:
        print()
        print("⚠️  配置不完整！请确保以下环境变量已设置：")
        print(f"   WX_APPID    = {'✅ 已设置' if CONFIG['APPID'] else '❌ 未设置'}")
        print(f"   WX_APPSECRET = {'✅ 已设置' if CONFIG['APPSECRET'] else '❌ 未设置'}")
        print(f"   WX_CLOUD_ENV = {'✅ 已设置' if CONFIG['CLOUD_ENV'] else '❌ 未设置'}")
        print()
        print("设置方法（在终端中执行）：")
        print('   export WX_APPID="你的AppID"')
        print('   export WX_APPSECRET="你的AppSecret"')
        print('   export WX_CLOUD_ENV="你的云环境ID"')
        print()
        sys.exit(1)

    # 检查目录
    if not os.path.isdir(data_dir):
        print(f"❌ JSON目录不存在: {data_dir}")
        sys.exit(1)

    # 获取 access_token
    print(f"\n🔐 正在获取 access_token...")
    token = get_access_token()
    if not token:
        print("\n❌ 无法获取 access_token，上传终止")
        print("   请检查 APPID 和 APPSECRET 是否正确")
        sys.exit(1)

    # 逐个上传
    success_count = 0
    fail_count = 0
    uploaded_data = {}  # v1.1：记录已成功上传的本地数据，用于后续回读校验

    for name in COLLECTIONS:
        filepath = os.path.join(data_dir, f'{name}.json')
        print(f"\n📤 上传 {name}...")

        if not os.path.exists(filepath):
            print(f"   ⚠️ 文件不存在: {filepath}，跳过")
            fail_count += 1
            continue

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 检查是否为降级数据
            if data.get('_fallback'):
                print(f"   ⚠️ {name} 为降级数据（提取时出错），跳过上传")
                fail_count += 1
                continue

            if upsert_data(name, date, data):
                print(f"   ✅ {name} 上传成功")
                success_count += 1
                uploaded_data[name] = data  # v1.1：记录本地数据用于校验
            else:
                print(f"   ❌ {name} 上传失败")
                fail_count += 1
        except json.JSONDecodeError as e:
            print(f"   ❌ JSON解析错误: {e}")
            fail_count += 1
        except Exception as e:
            print(f"   ❌ 未知错误: {e}")
            fail_count += 1

    # ─── v1.1 新增：上传后回读校验阶段 ────────────────────────────
    if uploaded_data:
        print(f"\n{'─' * 60}")
        print(f"🔍 上传后回读校验（共 {len(uploaded_data)} 个集合）...")
        print(f"{'─' * 60}")

        verify_pass = 0
        verify_fail = 0

        for name, local_data in uploaded_data.items():
            result = verify_upload(name, date, local_data)
            if result.get("ok"):
                print(f"   ✅ {name}: 云端字段完整，dataTime 一致")
                verify_pass += 1
            else:
                verify_fail += 1
                print(f"   ❌ {name}: 校验未通过")
                if result.get("error"):
                    print(f"      错误: {result['error']}")
                if result.get("missing_fields"):
                    print(f"      缺失字段: {result['missing_fields']}")
                if result.get("array_errors"):
                    print(f"      数组异常: {result['array_errors']}")
                if not result.get("dataTime_match"):
                    print(f"      ⚠️  dataTime 不一致（可能被截断或含特殊字符）")

        print(f"\n📋 校验结果: {verify_pass} 通过 / {verify_fail} 异常")
        if verify_fail > 0:
            print("   ⚠️  存在校验异常，建议检查云端数据或重新上传")
        print(f"{'─' * 60}")

    # ─── 总结 ─────────────────────────────────────────────────────
    print(f"\n{'=' * 60}")
    print(f"📊 上传结果: {success_count} 成功 / {fail_count} 失败 / {len(COLLECTIONS)} 总计")
    if fail_count == 0:
        print(f"🎉 全部上传成功！大老板打开小程序就能看到最新数据了 🦆")
    elif success_count > 0:
        print(f"⚠️ 部分上传成功，失败的数据将使用小程序本地缓存")
    else:
        print(f"❌ 全部上传失败，请检查配置和网络")
    print("=" * 60)

    sys.exit(0 if fail_count == 0 else 1)


if __name__ == '__main__':
    main()
