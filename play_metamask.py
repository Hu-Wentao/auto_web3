import asyncio
import re
from typing import Callable

from loguru import logger
from playwright.async_api import async_playwright, Page, BrowserContext


def find_page(context: BrowserContext, regex: str = '^(chrome-extension://)(.+)(#confirmation)$') -> Page:
    """在上下文中查找匹配的page;
    注意, 在这里无法获取到url的queryParam,只有url. 如`chrome-extension://.../home.html`"""
    for p in context.pages:
        if re.match(regex, p.url):
            return p
    raise RuntimeError(f"找不到匹配的page[{regex}],[{context.pages}]")


def debug_prd_page(reg: str) -> Callable[[Page], bool]:
    logger.debug(f'reg[{reg}]')

    def fn(page: Page) -> bool:
        logger.debug(f'debug_prd_page#[{page.url}]')
        return re.match(reg, page.url) is not None

    return fn


async def browser_init_metamask(context: BrowserContext, ext_id: str = None, debug=False) -> Page:
    """浏览器首次加载metamask插件时调用
    在已经进入MetaMask-钱包导入 页面的情况下, 开始导入助记词;
    - 由于钱包插件每次都会有不同的ext_id, 只有在新用户首次打开时,才会自动进入metamask钱包导入页面才可以获取插件id
    - 在插件页面(chrome-extension://), 似乎只能使用 query_selector
    :param debug: 调试page event
    :param context 浏览器上下文,可获取所有page
    :param ext_id 钱包插件id,todo 如果已有钱包插件id, 且钱包未初始化, 则进入钱包导入页面
    :return:
    """
    # metamask 欢迎页面
    # chrome-extension://paeponhgjlpkfdckogamhjefemceiegl/home.html#onboarding/welcome
    # page = find_page(context, regex='^(chrome-extension://)(.+)(#onboarding/welcome)$')
    # logger.debug(f'准备导入钱包')
    # 注意,expect_page获取url时,参数尚未加载,因此url截止到home.html
    # chrome-extension://paeponhgjlpkfdckogamhjefemceiegl/home.html
    reg_ext_welcome = '(chrome-extension://)(.+)(/home.html)'
    evt = (
        await context.expect_page(predicate=debug_prd_page(reg_ext_welcome), timeout=300_000).__aenter__()
    ) if debug else (
        await context.expect_page(predicate=lambda pg: re.match(reg_ext_welcome, pg.url) is not None).__aenter__()
    )

    page = await evt.value
    logger.debug(f'已进入钱包欢迎页[{page.url}]')
    # # 同意协议-复选框
    # # #onboarding__terms-checkbox
    await page.click(
        selector='#onboarding__terms-checkbox',
        no_wait_after=True, force=True, )
    logger.debug('已同意协议')
    # # 导入钱包按钮
    await page.click(
        selector='#app-content > div > div.mm-box.main-container-wrapper > div > div > div > ul > li:nth-child(3) > button',
    )
    logger.debug('已选择 导入钱包')
    # # 取消帮助提升metamask按钮
    await page.click(
        selector='#app-content > div > div.mm-box.main-container-wrapper > div > div > div > div.mm-box.onboarding-metametrics__buttons.mm-box--display-flex.mm-box--gap-4.mm-box--flex-direction-row.mm-box--width-full > button.mm-box.mm-text.mm-button-base.mm-button-base--size-lg.mm-button-secondary.mm-text--body-md-medium.mm-box--padding-0.mm-box--padding-right-4.mm-box--padding-left-4.mm-box--display-inline-flex.mm-box--justify-content-center.mm-box--align-items-center.mm-box--color-primary-default.mm-box--background-color-transparent.mm-box--rounded-pill.mm-box--border-color-primary-default.box--border-style-solid.box--border-width-1',
        timeout=2000
    )
    logger.debug('已点击 取消帮助提升metamask按钮')
    # # 导入助记词
    for i, w in enumerate(mnemonic.split(' ')):
        await page.fill(
            selector=f'#import-srp__srp-word-{i}',
            value=w,
            timeout=2000, )
    logger.debug('助记词页-已输入 助记词')
    # # 确认
    await page.click(
        selector='#app-content > div > div.mm-box.main-container-wrapper > div > div > div > div.import-srp__actions > div > button',
    )
    logger.debug('助记词页-已点击 确认')
    # # 设置密码
    # chrome-extension://nkbihfbeogaeaoehlefnkodbefgpgknn/home.html#onboarding/create-password
    await page.fill(
        selector='#app-content > div > div.mm-box.main-container-wrapper > div > div > div > div.mm-box.mm-box--margin-top-3.mm-box--justify-content-center > form > div:nth-child(1) > label > input',
        value=wallet_pwd,
        timeout=2000,
    )
    logger.debug('密码页-已设置 钱包密码')
    # # 确认密码

    await page.fill(
        selector='#app-content > div > div.mm-box.main-container-wrapper > div > div > div > div.mm-box.mm-box--margin-top-3.mm-box--justify-content-center > form > div:nth-child(2) > label > input',
        value=wallet_pwd,
        timeout=2000,
    )
    logger.debug('密码页-已确认 钱包密码')

    # # 同意协议
    await page.click(
        selector='#app-content > div > div.mm-box.main-container-wrapper > div > div > div > div.mm-box.mm-box--margin-top-3.mm-box--justify-content-center > form > div.mm-box.mm-box--margin-top-4.mm-box--margin-bottom-4.mm-box--justify-content-space-between.mm-box--align-items-center > label > span.mm-checkbox__input-wrapper > input',
        timeout=2000,
    )
    logger.debug('协议页-已同意 用户协议')

    await page.wait_for_timeout(1000)
    # # 导入钱包
    await page.click(
        selector='#app-content > div > div.mm-box.main-container-wrapper > div > div > div > div.mm-box.mm-box--margin-top-3.mm-box--justify-content-center > form > button',
        timeout=2000,
    )
    logger.debug('协议页-已确认 导入钱包')

    # == 点击 Go it
    await page.click(
        selector="#app-content > div > div.mm-box.main-container-wrapper > div > div > div > div.box.creation-successful__actions.box--margin-top-6.box--flex-direction-row > button")
    logger.debug('帮助页-已点击 Go it')
    # == 点击 Next
    await page.click(
        selector="#app-content > div > div.mm-box.main-container-wrapper > div > div > div > div.onboarding-pin-extension__buttons > button")
    logger.debug('提示页-已点击 Next')
    # == 点击 Done
    await page.click(
        selector="#app-content > div > div.mm-box.main-container-wrapper > div > div > div > div.onboarding-pin-extension__buttons > button")
    logger.debug('提示页-已点击 Done')
    logger.info('== 钱包导入完成 ==')
    return page
    pass


async def test_run(context: BrowserContext):
    page = await browser_init_metamask(context)

    await page.wait_for_timeout(5000_000)
    # === 到此处基本已经完成 ====


async def main_test():
    async with async_playwright() as playwright:
        context = await playwright.chromium.launch_persistent_context(
            user_data_dir,
            headless=False,
            args=[
                # "--headless=new", # 如果需要强行headless配置为new
                f"--disable-extensions-except={path_to_extension}",
                f"--load-extension={path_to_extension}",
            ],
        )
        await test_run(context)


if __name__ == '__main__':
    ext_name = f'metamask'
    path_to_extension = f"./extension/{ext_name}"
    user_data_dir = "./data/user39"
    mnemonic = 'mail author leaf language armed eight carbon confirm slam champion visa connect'
    wallet_pwd = '12345678'  # 钱包密码
    asyncio.run(main_test())
