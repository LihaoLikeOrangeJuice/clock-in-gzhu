import json
import os
import time
import traceback

import requests
import selenium.webdriver
from loguru import logger
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager


def launch_webdriver():
    options = Options()
    optionsList = [
        "--headless", "--enable-javascript", "start-maximized",
        "--disable-gpu", "--disable-extensions", "--no-sandbox",
        "--disable-browser-side-navigation", "--disable-dev-shm-usage"
    ]

    for option in optionsList:
        options.add_argument(option)

    options.page_load_strategy = 'eager'
    options.add_experimental_option(
        "excludeSwitches", ["ignore-certificate-errors", "enable-automation"])

    driver = selenium.webdriver.Chrome(service=Service(
        ChromeDriverManager().install()),
                                       options=options)

    return driver


def wd_login(xuhao, mima):
    driver = launch_webdriver()
    wdwait = WebDriverWait(driver, 30)
    s = requests.Session()

    # pageName用来表示当前页面标题
    # 0表示初始页面，Unified Identity Authentication页面，统一身份认证页面和其它页面
    pageName = 0

    # notification表示是否需要邮件通知打卡失败
    # 0表示不需要，1表示需要
    notification = 0

    for retries in range(10):
        try:
            logger.info(f"第{retries+1}次运行")
            refresh_times = 0

            if retries:
                while True:
                    logger.info('刷新页面')
                    driver.refresh()

                    title = driver.title
                    if title == '融合门户':
                        pageName = 1
                    elif title == '学生健康状况申报':
                        pageName = 2
                    elif title in ['填报健康信息 - 学生健康状况申报', '表单填写与审批::加载中']:
                        pageName = 3
                    elif title == "":
                        logger.info(f'当前页面标题为：{title}')

                        refresh_times += 1
                        if refresh_times < 4:
                            continue
                    else:
                        pageName = 0

                    break

                logger.info(f'当前页面标题为：{title}')

            if pageName == 0:
                logger.info('正在转到统一身份认证页面')
                driver.get(
                    f'https://newcas.gzhu.edu.cn/cas/login?service=https%3A%2F%2Fnewmy.gzhu.edu.cn%2Fup%2Fview%3Fm%3Dup'
                )

                wdwait.until(
                    EC.visibility_of_element_located(
                        (By.XPATH,
                         "//div[@class='robot-mag-win small-big-small']")))

                logger.info('正在尝试登陆融合门户')
                for script in [
                        f"document.getElementById('un').value='{xuhao}'",
                        f"document.getElementById('pd').value='{mima}'",
                        "document.getElementById('index_login_btn').click()"
                ]:
                    driver.execute_script(script)

            if pageName in [0, 1]:
                wdwait.until(
                    EC.visibility_of_element_located(
                        (By.XPATH, '//a[@title="健康打卡"]/img')))

                logger.info('正在转到学生健康状况申报页面')
                driver.get(
                    'https://yqtb.gzhu.edu.cn/infoplus/form/XNYQSB/start')

            if pageName in [0, 1, 2]:
                wdwait.until(
                    EC.element_to_be_clickable(
                        (By.ID, "preview_start_button"))).click()

                logger.info('正在转到填报健康信息 - 学生健康状况申报页面')

            if pageName in [0, 1, 2, 3]:
                wdwait.until(
                    EC.element_to_be_clickable(
                        (By.XPATH,
                         "//div[@align='right']/input[@type='checkbox']")))

                cookies = driver.get_cookies()
                for cookie in cookies:
                    s.cookies.set(cookie['name'], cookie['value'])

                referer = driver.current_url
                csrfToken = driver.find_element(
                    By.XPATH,
                    "//meta[@itemscope='csrfToken']").get_attribute("content")
                stepId = referer.split("/")[-2]

                break
        except Exception:
            logger.error(traceback.format_exc())
            logger.error(f"第{retries+1}次运行失败")

            # retries == 9代表最后一次循环，如果这次循环仍然异常，则
            if retries == 9:
                notification = 1

    driver.quit()

    for retries in range(10):
        try:
            render_data = {
                "stepId": stepId,
                "instanceId": "",
                "admin": "false",
                "rand": "774.7022920739238",
                "width": "432",
                "lang": "en",
                "csrfToken": csrfToken
            }

            headers = {
                "User-Agent":
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.64 Safari/537.36 Edg/101.0.1210.53",
                "Referer": referer,
            }

            render_url = "https://yqtb.gzhu.edu.cn/infoplus/interface/render"
            render_page = s.post(render_url, headers=headers, data=render_data)

            formData = json.loads(render_page.content)['entities'][0]['data']
            formData["fieldJBXXdrsfwc"] = '2'
            formData['fieldSTQKbrstzk1'] = '1'
            formData['fieldJKMsfwlm'] = '1'
            formData['fieldYQJLsfjcqtbl'] = '2'
            formData['fieldCXXXsftjhb'] = '2'
            formData['fieldCNS'] = True

            json_formData = json.dumps(formData)

            doAction_data = {
                "stepId": stepId,
                "actionId": "1",
                "remark": "",
                "formData": json_formData,
                "timestamp": str(int(time.time())),
                "rand": "170.51853138736112",
                "nextUsers": "{}",
                "boundFields":
                "fieldSTQKzdjgmc,fieldSTQKjtcyglkssj,fieldYMTGSzd,fieldCXXXsftjhb,fieldJCDDqmsjtdd,fieldYQJLksjcsj,fieldSTQKjtcyzd,fieldJBXXjgsjtdz,fieldSTQKbrstzk,fieldSTQKfrtw,fieldSTQKjtcyqt,fieldCXXXjtfslc,fieldJBXXlxfs,fieldSTQKxgqksm,fieldSTQKpcsj,fieldJKMsfwlm,fieldJKHDDzt,fieldYQJLsfjcqtbl,fieldYQJLzhycjcsj,fieldSTQKfl,fieldSTQKhxkn,fieldJBXXbz,fieldCXXXsfylk,fieldFLid,fieldjgs,fieldSTQKglfs,fieldCXXXsfjcgyshqzbl,fieldSTQKjtcyfx,fieldCXXXszsqsfyyshqzbl,fieldJCDDshi,fieldSTQKrytsqkqsm,fieldJCDDs,fieldSTQKjtcyfs,fieldSTQKjtcyzljgmc,fieldSQSJ,fieldJZDZC,fieldJBXXnj,fieldSTQKjtcyzdkssj,fieldSTQKfx,fieldSTQKfs,fieldYQJLjcdry,fieldCXXXjtfsdb,fieldCXXXcxzt,fieldYQJLjcddshi,fieldCXXXjtjtzz,fieldCXXXsftjhbs,fieldHQRQ,fieldSTQKjtcyqtms,fieldCXXXksjcsj,fieldSTQKzdkssj,fieldSTQKfxx,fieldSTQKjtcyzysj,fieldjgshi,fieldSTQKjtcyxm,fieldJBXXsheng,fieldZJYCHSJCYXJGRQzd,fieldJBXXdrsfwc,fieldqjymsjtqk,fieldJBXXdw,fieldCXXXjcdr,fieldCXXXsftjhbjtdz,fieldJCDDq,fieldSFJZYM,fieldSTQKjtcyclfs,fieldSTQKxm,fieldCXXXjtgjbc,fieldSTQKjtcygldd,fieldSTQKjtcyzdjgmcc,fieldSTQKzd,fieldSTQKqt,fieldCXXXlksj,fieldSTQKjtcyfrsj,fieldCXXXjtfsqtms,fieldSTQKjtcyzdmc,fieldCXXXjtfsfj,fieldJBXXfdy,fieldSTQKjtcyjmy,fieldJBXXxm,fieldJKMjt,fieldSTQKzljgmc,fieldCXXXzhycjcsj,fieldCXXXsftjhbq,fieldSTQKqtms,fieldYCFDY,fieldJBXXxb,fieldSTQKglkssj,fieldCXXXjtfspc,fieldSTQKbrstzk1,fieldYCBJ,fieldCXXXssh,fieldSTQKzysj,fieldLYYZM,fieldJBXXgh,fieldCNS,fieldCXXXfxxq,fieldSTQKclfs,fieldSTQKqtqksm,fieldCXXXqjymsxgqk,fieldYCBZ,fieldSTQKjmy,fieldSTQKjtcyxjwjjt,fieldJBXXxnjzbgdz,fieldSTQKjtcyfl,fieldSTQKjtcyzdjgmc,fieldCXXXddsj,fieldSTQKfrsj,fieldSTQKgldd,fieldCXXXfxcfsj,fieldJBXXbj,fieldSTQKjtcyfxx,fieldSTQKks,fieldJBXXcsny,fieldCXXXjtzzq,fieldJBXXJG,fieldCXXXdqszd,fieldCXXXjtzzs,fieldJBXXshi,fieldSTQKjtcyfrtw,fieldSTQKjtcystzk1,fieldCXXXjcdqk,fieldSTQKzdmc,fieldSFJZYMyczd,fieldSTQKjtcyks,fieldSTQKjtcystzk,fieldCXXXjtfshc,fieldYMTGSzdqt,fieldCXXXcqwdq,fieldSTQKxjwjjt,fieldSTQKjtcypcsj,fieldJBXXqu,fieldSTQKlt,fieldYMJZRQzd,fieldJBXXjgshi,fieldYQJLjcddq,fieldYQJLjcdryjkqk,fieldYQJLjcdds,fieldSTQKjtcyhxkn,fieldCXXXjtzz,fieldJBXXjgq,fieldCXXXjtfsqt,fieldJBXXjgs,fieldSTQKjtcylt,fieldSTQKzdjgmcc,fieldJBXXqjtxxqk,fieldDQSJ,fieldSTQKjtcyglfs,",
                "csrfToken": csrfToken,
                "lang": "en"
            }

            doAction_url = "https://yqtb.gzhu.edu.cn/infoplus/interface/doAction"
            doAction_page = s.post(doAction_url,
                                   headers=headers,
                                   data=doAction_data)

            if (json.loads(doAction_page.content)["error"]) == "打卡成功":
                logger.info("健康打卡成功")
                logger.info(doAction_page.text)
                break
            else:
                logger.error("健康打卡失败")
                logger.error(doAction_page.text)

                logger.info("重新进行打卡")
        except Exception:
            logger.error(traceback.format_exc())
            logger.error(f"第{retries+1}次运行失败")

            # retries == 9代表最后一次循环，如果这次循环仍然异常，则
            if retries == 9:
                notification = 1

    if notification == 1:
        logger.critical('打卡失败，尝试抛出异常，以便github邮件通知打卡失败')
        a = '12'
        a.append(a)


if __name__ == "__main__":
    xuhao = str(os.environ['XUHAO'])
    mima = str(os.environ['MIMA'])

    wd_login(xuhao, mima)
