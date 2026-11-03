import runtime from 'luci.runtime';
import { entityencode, striptags } from 'html';
import { cursor } from 'uci';

const words = { 'Username': '用户名', 'Password': '密码', 'Log in': '查看概览预览', 'Toggle navigation': '展开导航' };
const env = {
    _: s => words[s] ?? s,
    entityencode, striptags,
    ubus: { call: () => ({ hostname: 'TR1200-Personal' }) },
    http: {
        closed: false,
        write: (...args) => print(...args),
        prepare_content: () => null,
        urlencode: s => s,
        getenv: () => './overview.html'
    },
    dispatcher: {
        lang: 'zh-cn',
        build_url: (...args) => '/cgi-bin/luci/' + join('/', args),
        lookup: () => true,
        error500: msg => die(msg)
    },
    ctx: { path: ['admin', 'status', 'overview'], request_path: ['admin', 'status', 'overview'], authsession: 'local-preview' },
    node: null,
    dispatched: { title: '概览' },
    duser: '',
    fuser: null,
    version: {
        luciname: 'LuCI', luciversion: '25.12',
        distname: 'OpenWrt', distversion: '25.12.5', distrevision: 'UI Preview',
        disturl: 'https://openwrt.org/'
    }
};

const rt = runtime(env);
if (ARGV[0] == 'login') {
    rt.render('themes/argon/sysauth');
} else {
    rt.render('themes/argon/header');
    print('<div class="preview-notice">界面预览 · 以下为示例内容，未连接路由器</div>');
    print('<div id="view"><h2>概览</h2><div class="cbi-section"><h3>系统</h3><table class="table">');
    for (let row in [
        ['主机名', 'TR1200-Personal'],
        ['型号', 'Cudy TR1200 v1'],
        ['系统', 'OpenWrt 25.12.5 · 中文 LuCI'],
        ['界面', 'Argon 3.1.2'],
        ['运行时间', '示例 · 2 小时 18 分钟'],
        ['平均负载', '示例 · 0.03 / 0.02 / 0.00']
    ]) print('<tr class="tr"><td class="td left">', row[0], '</td><td class="td left">', row[1], '</td></tr>');
    print('</table></div><div class="cbi-section"><h3>内存</h3><div class="cbi-section-node preview-memory"><p>可用内存 · 示例</p><div class="cbi-progressbar" title="72 MiB / 120 MiB"><div style="width:60%"></div></div></div></div>');
    print('<div class="cbi-section"><h3>网络</h3><table class="table"><tr class="tr"><td class="td left">管理方式</td><td class="td left">有线 / HTTPS</td></tr><tr class="tr"><td class="td left">无线</td><td class="td left">双频 · 按需配置</td></tr><tr class="tr"><td class="td left">在线壁纸</td><td class="td left">关闭</td></tr></table></div></div>');
    rt.render('themes/argon/footer');
}
