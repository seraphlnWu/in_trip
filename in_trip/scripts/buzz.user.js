// ==UserScript==
// @name    BuzzMaster-XPATH标注工具
// @namespace http://www.admaster.com.cn
// @description 生成结点的XPATH,用于抽取。 
// @include *
// @exclude http://www.admaster.com.cn/*
// @resource jquery.alerts.css http://116.213.213.90:8080/static/css/jquery.alerts.css
// @require http://ajax.googleapis.com/ajax/libs/jquery/1.8.3/jquery.min.js 
// @require http://116.213.213.90:8080/static/js/jquery.alerts.js 
// @require http://116.213.213.90:8080/static/js/jquery-ui-1.9.2.custom.min.js
// ==/UserScript==

var alertCss = GM_getResourceText("jquery.alerts.css");
GM_addStyle(alertCss);
var HOST = "http://116.213.213.90:8080";
//var HOST = "http://127.0.0.1:8080";
var SUBMIT_URL = HOST + "/xpath/add";
var CHECK_URL = HOST + "/url_regex/check";
var VALIDATE_URL = HOST + '/xpath/validate';
var CHECK_FOR_EXIST = HOST +"/xpath/check_for_exist";

var INTERFACE_HTML = '\
    <style>\
        .field {clear:both;margin-top:5px;margin-bottom:5px;}\
        .field_label {display:block;float:left;width:120px;text-align:right;margin-right:5px;}\
        .section_content {border-top:1px dotted black;margin-top:5px;margin-bottom:5px;padding-top:2px;padding-bottom:2px;}\
        input[type=text] {width:480px;}\
        .dynDiv_moveDiv { cursor: move; position: absolute; overflow: hidden; }\
        .dynDiv_resizeDiv_tl,.dynDiv_resizeDiv_tr,.dynDiv_resizeDiv_bl,.dynDiv_resizeDiv_br { width: 6px; height: 6px; background: #faa; border: 1px solid #000; position: absolute; }\
        .dynDiv_resizeDiv_tl { top: -1px; left: -1px; }\
        .dynDiv_resizeDiv_tr { top: -1px; right: -1px; }\
        .dynDiv_resizeDiv_bl { bottom: -1px; left: -1px; }\
        .dynDiv_resizeDiv_br { bottom: -0.1px; right: -0.1px; }\
        .dynDiv_moveParentDiv { width: 100%; margin: auto; height: 16px; font-size: 15px; position: absolute; top: -1px; left: -1px; background: #faa; border: 1px solid #aaa; border-left: 0; border-right: 0; padding: 0; overflow: hidden; white-space:nowrap; }\
        .dynDiv_minmaxDiv { position: absolute; top: 1px; right: 15px; width: 15px; height: 15px; background: #faa; font-size: 15px; padding: 0; margin: 0; }\
        .first {text-align:right;width:10%;}\
        table {width:100%;}\
        table tr {heigth:42px;}\
        table td {width:40%;}\
        .tip {color:red;}\
    </style>\
    <div style="overflow-y:auto;">\
    <div class="section" id="xpath-info">\
        <p>XPath<span style="position:fixed;right:20%;top:6px;"><input type="checkbox" name="url_xpath_button" id="url_xpath_button"/>url抽取</span><button id="expand" style="position:fixed;right:13%;top:6px;">展开</button></p>\
        <div class="section_content">\
            <form>\
                <div class="field">\
                    <label for="xpath" class="field_label" style="height:60px;">XPath:</label>\
                    <input type="text" name="xpath_1" id="xpath_1"/><input type="checkbox" name="xpath" value="xpath_1" checked/>\
                    <input type="text" name="xpath_2" id="xpath_2"/><input type="checkbox" name="xpath" value="xpath_2"/>\
                </div>\
                <div class="field">\
                    <label for="xpath_regex" class="field_label">XPath正则:</label>\
                    <input type="text" name="xpath_regex" id="xpath_regex"/>\
                    <button class="xpath_regex" cls=".*?(\\d{4}).*?(\\d{1,2}).*?(\\d{1,2}).*~\\1-\\2-\\3">年月日</button>\
                    <button class="xpath_regex" cls=".*?(\\d{4}).*?(\\d{1,2}).*?(\\d{1,2}).*?(\\d{1,2}).*?(\\d{1,2}).*~\\1-\\2-\\3 \\4:\\5">年月日时分</button>\
                    <button class="xpath_regex" cls=".*?(\\d{4}).*?(\\d{1,2}).*?(\\d{1,2}).*?(\\d{1,2}).*?(\\d{1,2}).*?(\\d{1,2}).*~\\1-\\2-\\3 \\4:\\5:\\6">年月日时分秒</button>\
                </div>\
                <div class="field">\
                    <label for="column" class="field_label">字段:</label>\
                    <select name="column" id="column">\
                        <option value="title">标题</option>\
                        <option value="time">时间</option>\
                        <option value="content">正文</option>\
                        <option value="author">作者</option>\
                        <option value="reply">回复数</option>\
                        <option value="view">浏览数</option>\
                    </select>\
                    <button id="xpath_test">测试</button>\
                    <button id="xpath_save">保存</button>\
                </div>\
            </form>\
        </div>\
    </div>\
    <div class="section" id="site-info">\
        <p>网站信息</p>\
        <div class="section_content">\
            <form>\
                <div class="field">\
                    <label for="seed_url" class="field_label">网站URL:</label>\
                    <input type="text" name="seed_url" id="seed_url"/>\
                </div>\
                <div class="field">\
                    <label for="url_regex" class="field_label">URL正则:</label>\
                    <input type="text" name="url_regex" id="url_regex"/><button id="check_available">检查</button><span id="check_tip" class="tip"></span>\
                </div>\
                <div class="field">\
                    <label for="site_type" class="field_label">网站类型:</label>\
                    <select name="site_type" id="site_type">\
                        <option value="新闻">新闻</option>\
                        <option value="博客">博客</option>\
                        <option value="论坛">论坛</option>\
                        <option value="SNS">SNS</option>\
                        <option value="微博">微博</option>\
                        <option value="视频">视频</option>\
                    </select>\
                </div>\
                <div class="field">\
                    <label for="site_name" class="field_label">网站名称:</label>\
                    <input type="text" name="site_name" id="site_name"/>\
                </div>\
                <div class="field">\
                   <label for="industry" class="field_label">行业:</label>\
                   <select name="industry" id="industry"/>\
                        <option value="IT">IT</option>\
                        <option value="电子商务">电子商务</option>\
                        <option value="房地产">房地产</option>\
                        <option value="服装">服装</option>\
                        <option value="卫浴美容">卫浴美容</option>\
                        <option value="家居装饰">家居装饰</option>\
                        <option value="教育">教育</option>\
                        <option value="金融">金融</option>\
                        <option value="旅游">旅游</option>\
                        <option value="零售购物">零售购物</option>\
                        <option value="媒体">媒体</option>\
                        <option value="女性">女性</option>\
                        <option value="汽车交通">汽车交通</option>\
                        <option value="餐饮">餐饮</option>\
                        <option value="文化体育">文化体育</option>\
                        <option value="数码通讯" >数码通讯</option>\
                        <option value="医疗健康">医疗健康</option>\
                        <option value="游戏">游戏</option>\
                        <option value="母婴">母婴</option>\
                        <option value="其他">其他</option>\
                   </select>\
                </div>\
                <div class="field">\
                    <label for="charset" class="field_label">编码:</label>\
                    <select name="charset" id="charset">\
                        <option value="">默认</option>\
                        <option value="utf-8">utf-8</option>\
                        <option value="cp936">cp936</option>\
                    </select>\
                    <button id="site_test">测试</button>\
                    <button id="site_save">保存</button>\
                </div>\
            </form>\
        </div>\
    </div>\
    <div class="section" id="saved-info">\
        <p>准备提交的信息</p>\
        <div class="section_content">\
            <table>\
                <tr id="site_row">\
                    <td class="first"><span style="color:red;">*</span>URL:</td>\
                    <td class="essential necessary"></td>\
                    <td></td>\
                </tr>\
                <tr id="site_type_row">\
                    <td class="first"><span style="color:red;" class="hide_show">*</span>类型:</td>\
                    <td class="essential"></td>\
                    <td></td>\
                </tr>\
                <tr id="site_name_row">\
                    <td class="first"><span style="color:red;" class="hide_show">*</span>网站名称:</td>\
                    <td class="essential"></td>\
                    <td></td>\
                </tr>\
                <tr id="title_row">\
                    <td class="first"><span style="color:red;" class="hide_show">*</span>标题:</td>\
                    <td class="essential"></td>\
                    <td></td>\
                </tr>\
                <tr id="time_row">\
                    <td class="first"><span style="color:red;" class="hide_show">*</span>时间:</td>\
                    <td class="essential"></td>\
                    <td></td>\
                </tr>\
                <tr id="content_row">\
                    <td class="first"><span style="color:red;" class="hide_show">*</span>正文:</td>\
                    <td class="essential"></td>\
                    <td></td>\
                </tr>\
                <tr id="author_row">\
                    <td  class="first">作者:</td>\
                    <td></td>\
                    <td></td>\
                </tr>\
                <tr id="reply_row">\
                    <td  class="first">回复:</td>\
                    <td></td>\
                    <td></td>\
                </tr>\
                <tr id="view_row">\
                    <td  class="first">浏览:</td>\
                    <td></td>\
                    <td></td>\
                </tr>\
                <tr id="industry_row">\
                    <td  class="first">行业:</td>\
                    <td></td>\
                    <td></td>\
                </tr>\
                <tr id="charset_row">\
                    <td  class="first">编码:</td>\
                    <td></td>\
                    <td></td>\
                </tr>\
            </table>\
        </div>\
        <div style="margin-left:auto;margin-right:auto;width:100%;">\
            <button id="total_test">测试全部</button>\
            <button id="total_submit">全部提交</button>\
            <span id="tip" class="tip"></span>\
        </div>\
    </div>\
    </div>\
    <div class="dynDiv_resizeDiv_br"></div>\
'

var CAN_SUBMIT=false;
function prepareForm() {
    var div = document.createElement('div');
    div.setAttribute("id", "buzz-xpath");
    //div.setAttribute("ignore", "true");
    div.innerHTML = INTERFACE_HTML;
    ignoreNode(div);
    div.style.cssText = "position:absolute;top:0px;zoom:1;z-index:100001;background:whiteSmoke;border:1px solid #785;width:80%;left:10%;right:10%;padding-top:10px;overflow-y:auto;display:none;height:180px;";
    insertAfter(div, document.body.lastChild);
}

function ignoreNode(node) {
    node.setAttribute('ignore', 'true');
    var childrens = node.childNodes;
    for (var i=0;i < childrens.length; i++) {
        if (childrens[i].nodeType == 1) {
            if (childrens[i].childElementCount  > 0)
                ignoreNode(childrens[i]);
            else
                childrens[i].setAttribute('ignore', 'true');
        }
    }
}

function prepareBorder() {
    var border_div = document.createElement('div');
    border_div.innerHTML = '\
        <style>\
            .bor {position:absolute;zoom:1;z-index:10000;}\
        </style>\
        <div id="bor-top" class="bor"></div>\
        <div id="bor-right" class="bor"></div>\
        <div id="bor-bottom" class="bor"></div>\
        <div id="bor-left" class="bor"></div>\
        ';
    insertAfter(border_div, document.body.lastChild);
}


function addSideBar() {
    var side_bar = document.createElement('div');
    side_bar.setAttribute('id', 'side_bar');
    side_bar.setAttribute('ignore', 'true');
    side_bar.innerHTML = "显示抽取工具";
    side_bar.style.cssText = "position:fixed;left:0;top:48%;width:24px;border:1px solid red;color:#072;background:#E9F1E8;z-index:9999;"
    insertAfter(side_bar, document.body.lastChild);
}

function drawBorder(target) {
    var width = target.offsetWidth;
    var height = target.offsetHeight;
    var pos = $(target).offset();
    var body_pos = $('body').offset();
    //if (typeof $(target).attr('own') === 'undefined') {
    //   if ($(target).attr('class') == 'text_past') {
    //        color = "blue";
    //    }
    //    else {
    //    }
            color = "red";
            $('#bor-top').css({"background":color,"left":pos.left - body_pos.left,"top":pos.top - body_pos.top,"width":width,"height":1});
            $('#bor-bottom').css({"background":color,"left":pos.left - body_pos.left,"top":pos.top - body_pos.top + height,"width":width,"height":1});
            $('#bor-left').css({"background":color,"left":pos.left - body_pos.left,"top":pos.top - body_pos.top ,"width":1,"height":height});
            $('#bor-right').css({"background":color,"left":pos.left - body_pos.left + width,"top":pos.top - body_pos.top,"width":1,"height":height});
}

function handleClick(e) {
    if (!e.target.getAttribute("ignore")) {
        var xpath_1 = addPrefix(getXPath(e.target, 0)) + "/text()";
        var xpath_2 = addPrefix(getXPath(e.target, 1000)) + '/text()';
        //jAlert(xpath);
        $('input[name=xpath_1]').val(xpath_1);
        $('input[name=xpath_2]').val(xpath_2);
        $('input[name=xpath_regex]').val('');
    }
}

function getElements(node, tagName, className) {
    var children = (node || document).getElementsByTagName(tagName || '*');
    var elements = new Array();
    for (var i=0; i<children.length; i++){
        var child = children[i];
        if (child.parentNode != node)
            continue;
        if (className) {
            if (child.className == className){ 
                elements.push(child);
            }
        } else {
            elements.push(child);
        }
    } 
    return elements;
};

Array.prototype.indexOf = function (element) {
    for (var i=0; i < this.length; i++) {
        if (this[i] == element) 
            return i;
    }
    return -1;
}

function getXPath(node, deepth) {
    if (typeof(node) == undefined || node.tagName == undefined) {
        return "";
    } else if (deepth<=0 && node.id)
        return node.tagName.toLowerCase() + "[@id='" + node.id + "']";
    else if (node.className) {
    //if (node.className) {
        var total_count = document.getElementsByClassName(node.className).length;
        var sibling = getElements(node.parentNode, node.tagName, node.className);
        var all_sibling = getElements(node.parentNode, node.tagName);
        //jAlert(sibling.indexOf(node));
        if (total_count != sibling.length) {
            //return getXPath(node.parentNode, --deepth) + '/' + node.tagName.toLowerCase() + "[@class='" + node.className + "']["+ (sibling.indexOf(node) + 1).toString() + "]";
            return getXPath(node.parentNode, --deepth) + '/' + node.tagName.toLowerCase() + "["+ (all_sibling.indexOf(node) + 1).toString() + "]";
        } else {
            if (sibling.length > 1)
                return node.tagName.toLowerCase() + "[@class='" + node.className + "']["+ (sibling.indexOf(node) + 1).toString() + "]";
            else
                return node.tagName.toLowerCase() + "[@class='" + node.className + "']";
        }
    } else {
        var sibling = getElements(node.parentNode, node.tagName);
        var xpath = '';
        if (sibling.length > 1)
            xpath = node.tagName.toLowerCase() + "[" + (sibling.indexOf(node) + 1).toString() + "]";
        else 
            xpath = node.tagName.toLowerCase();
        //jAlert(xpath);
        return getXPath(node.parentNode, --deepth) + '/' + xpath;
    }
}


function addPrefix(xpath) {
    if (xpath.substr(0,5) != "/html") {
        xpath = "//" + xpath;
    } 
    /*else {
        xpath = "/" + xpath;
    } */
    return xpath
}

function insertAfter(newNode, referenceNode) {
        var parent_node = referenceNode.parentNode;
        if (parent_node.lastChild == referenceNode) {
            parent_node.appendChild(newNode);
        } else {
            parent_node.insertBefore(newNode, referenceNode.nextSibling);
        } 
}

//重载a标签的click事件，防止跳转
function disableLink(e) {
    //$('a').click(function(e) {
    e.preventDefault();
    handleClick(e);
    return false;
    //});
}




function mouseOverHandle(e) {
    if (!e.target.getAttribute("ignore")) 
        drawBorder(e.target);
}

$("#side_bar").live('click', function (e) {
//toggle(function (e) {
    $(document).bind('mouseover', mouseOverHandle);

    $(document).bind('click', handleClick);

    $("#buzz-xpath").show();
    $('a').bind('click', disableLink);
    $(this).text("隐藏抽取工具");
    $(this).attr('id', 'hide_side_bar');
});

$("#hide_side_bar").live('click', function (e) {
    $(document).unbind('mouseover', mouseOverHandle);

    $(document).unbind('click', handleClick);

    $("#buzz-xpath").hide();
    $('a').unbind('click', disableLink);
    $(this).text("显示抽取工具")
    $(this).attr('id', 'side_bar');
});

$("#expand").live('click', function (e) {
    $("#buzz-xpath").css("height", $('#buzz-xpath')[0].scrollHeight);
    $(this).attr('id', 'contract');
    $(this).text('收缩');
    return false;
});

$("#contract").live('click', function(e) {
    $("#buzz-xpath").css("height", "180px");
    $(this).attr('id', 'expand');
    $(this).text('展开');
    return false;
});

function calXPathResult(xpath, regex){
    var msg = "";
    if (regex)
        regex = transform_regex(regex)
 
    try {
        var xpath_results = document.evaluate(xpath.replace(/&nbsp;/g, "\xa0"), document.documentElement, null, XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);
    } catch (e) {
        msg = "xpath 有语法错误";
        return msg;
    }
    if (xpath_results) {
        msg = '';
        for (var i=0;i < xpath_results.snapshotLength; i++) 
            msg += xpath_results.snapshotItem(i).textContent.replace(/[\n\s\r]/g, " ") + "\n";

        if (regex) {
            if (regex.length > 1) {
                msg = msg.replace(/[\n\s\r]/g, " ").replace(new RegExp(regex[0]), regex[1]);
            } else { 
                match = msg.replace(/[\n\s\r]/g, " ").match(regex[0]);
                if (match)
                    msg =  match[1] + "\n";
                else
                    msg = "正则不匹配\n";
            }
        }
        //msg = "一共" + xpath_results.snapshotLength + "个结果\n" + msg.replace(/[\n\s\r]/g, ' ');
        msg = "一共" + xpath_results.snapshotLength + "个结果\n" + msg;
    }
    return msg;
}

function getAllXPath() {
    var xpath_options = [];
    var xpaths = [];
    var option;
    $(':checkbox[name=xpath][checked]').each(function () {
        xpath_options.push($(this).val());
    });
    
    for (option in xpath_options) {
        //console.log(xpath_options[option]);
        xpaths.push($("input[name=" + xpath_options[option] + "]").val());
    } 
    return xpaths;
}

function transform_regex(regex) {
    regex = regex.split('~');
    if (regex.length > 1)
        regex[1] = regex[1].replace(/\\/g, "$");
    return regex;

}
$("#xpath_test").live('click', function (e) {
    var msg = '';
    var xpaths = getAllXPath();
    var regex = $('input[name=xpath_regex]').val();
    if (xpaths.length < 1)
        return false;
    if (xpaths.length == 1) { 
        msg = calXPathResult(xpaths[0], regex); 
    } else {
        for (var i = 0; i < xpaths.length;i++) {
            msg += "xpath" + i + calXPathResult(xpaths[i], regex); 
        }
    }
    jAlert(msg)
    return false;
});

$('#xpath_save').live('click', function (e) {
    //var xpath = $('input[name=xpath]').val();
    var xpath = getAllXPath();
    var content = '';
    var regex = $('input[name=xpath_regex]').val();
    var column = $('select[name=column] :selected').val();
    var row = $("#" + column + "_row").children();
    for (var i=0;i<xpath.length;i++) {
        var date = new Date();
        var id = date.getTime() + i * 10;
        content += '<p ignore="true" id="' + id + '"><span ignore="ture">' + xpath[i] + '</span><a href="javascript:void(0)" class="del_xpath" ignore="true" cls="' + id + '">&nbsp;&nbsp;删除</a></p>';
    }
    //content = content.join('<br/>');
    //if (row.eq(1).html())
    //    content = '<br/>' + content;
    row.eq(1).html(row.eq(1).html() + content);
    //row.eq(2).html(row.eq(2).html() + regex + '<br/>');
    /*if (regex) {
        regex = regex.split('~');
	regex = "s/" + regex.join('/') + '/';
    }*/
    row.eq(2).text(regex);
    $("#column").get(0).selectedIndex = $("#column").get(0).selectedIndex + 1;
    return false;
});

$('#site_test').live('click', function (e) {
    var seed_url = $('input[name=seed_url]').val().split('___')[0].replace(/https?:\/\//, "");
    var url_regex = $('input[name=url_regex]').val();
    var matchs = seed_url.match(url_regex);
    var msg = '不匹配';
    if (matchs)
        msg = matchs[0];
    jAlert(msg);
    return false;
});

$('#site_save').live('click', function (e) {
    var seed_url = $('input[name=seed_url]').val();
    var url_regex = $('input[name=url_regex]').val();
    if (url_regex.length > 0 && !seed_url.split('___')[0].replace(/https?:\/\//, "").match(url_regex)) {
    	jAlert('正则不匹配');
	return false;
    }
    var row = $("#site_row").children();
    row.eq(1).text(seed_url);
    row.eq(2).text(url_regex);

    var site_type = $('select[name=site_type] :selected').val();
    var row = $("#site_type_row").children();
    row.eq(1).text(site_type);

    var site_name = $('input[name=site_name]').val();
    var row = $("#site_name_row").children();
    row.eq(1).text(site_name);

    var charset = $('select[name=charset] :selected').val();
    var row = $("#charset_row").children();
    row.eq(1).text(charset);

    var industry = $("select[name=industry] :selected").val();
    var row = $("#industry_row").children();
    row.eq(1).text(industry);

    return false;
});

$(".del_xpath").live('click', function (e) {
    //var pNode = $(this).parent().parent();
    //jAlert(pNode.html());
    var id = $(this).attr('cls');
    $("#"+id).remove();
    //$(this).remove();
    //if (pNode.html().match("/<br>$/"))
    //    var origin = pNode.html();
    //    pNode.html(origin.substring(0, (origin.length - 5)));
    return false;
});

function checkEssential() {
    var pass = true;
    $(".essential").each(function () {
        if (!$(this).text())
            pass = false;
    });
    return pass;
}

function checkNessary() {
    var pass = true;
    $('.necessary').each(function () {
        if (!$(this).text())
            pass = false;
    });
    return pass;
}
function getSubmittedData() {
    var data = "";
    var site_row = $("#site_row").children();
    data += "eg=" + encodeURIComponent(site_row.eq(1).text()) + "&";
    data += "url_reg=" + encodeURIComponent(site_row.eq(2).text()) + "&";

    var site_type_row = $("#site_type_row").children();
    data += "ctgry=" + site_type_row.eq(1).text() + "&";

    var site_name_row = $('#site_name_row').children();
    data += "domain=" + site_name_row.eq(1).text() + "&";

    var title_row = $("#title_row").children();
    var time_row = $("#time_row").children();
    var content_row = $("#content_row").children();
    var author_row = $("#author_row").children();
    var reply_row = $('#reply_row').children();
    var view_row = $('#view_row').children();
    var industry_row = $('#industry_row').children();
    var charset_row = $('#charset_row').children();
    var reg = /\(([^()]*?)\)/g;
    var order_reg = /\d/g;

    if (title_row.eq(1).text()) {
        data += getAll(title_row.eq(1), "title") + "&";
        var raw_title_regex = title_row.eq(2).text();
        var title_regex = '';
        if (raw_title_regex.length>0) {
            title_regex = raw_title_regex.split('~')[0];
            title_regex = title_regex.replace(reg, '\(?P<title>$1\)');
        }
        data += "title_regex=" + encodeURIComponent(title_regex) + "&"; 
    }
    if (time_row.eq(1).text()) {
        data += getAll(time_row.eq(1), "at") + '&';
        var raw_at_regex = time_row.eq(2).text();
        var at_regex = '';
        var order = '';
        if (raw_at_regex.length>0) {
            at_regex = raw_at_regex.split('~')[0];
            order = raw_at_regex.split('~')[1];
            var name_dict={'1':'year', '2':'month', '3':'day', '4':'hour', '5':'minute', '6':'second'};
            var matches = at_regex.match(reg);
            var order_matches = order.match(order_reg);
            var i = 0;
            while (i<matches.length) {
                slice_point = at_regex.indexOf(matches[i]);
                at_regex = at_regex.slice(0, slice_point+1)+'?P<'+name_dict[order_matches[i]]+'>'+at_regex.slice(slice_point+1);
                i = i + 1;
            }
        }
        data += 'at_regex=' + encodeURIComponent(at_regex) + "&";
    }

    if (content_row.eq(1).text()) {
        data += getAll(content_row.eq(1), 'src') + "&";
        var raw_src_regex = content_row.eq(2).text();
        var src_regex = '';
        if (raw_src_regex.length>0) {
            src_regex = raw_src_regex.split('~')[0];
            src_regex = src_regex.replace(reg, '\(?P<content>$1\)');
        }
        data += "src_regex=" + encodeURIComponent(src_regex) + '&';
    }

    if (author_row.eq(1).text()) {
        data += getAll(author_row.eq(1), 'authr') + '&';
        var raw_authr_regex = author_row.eq(2).text();
        var authr_regex = '';
        if (raw_authr_regex.length>0) {
            authr_regex = raw_authr_regex.split('~')[0];
            authr_regex = authr_regex.replace(reg, '\(?P<author>$1\)');
        }
        data += "authr_regex=" + encodeURIComponent(authr_regex) + "&";
    }

    if (view_row.eq(1).text()) {
        data += getAll(view_row.eq(1), 'views') + '&';
        var raw_views_regex = view_row.eq(2).text();
        var views_regex = '';
        if (raw_views_regex.length>0) {
            views_regex = raw_views_regex.split('~')[0];
            views_regex = views_regex.replace(reg, '\(?P<view_count>$1\)');
        }
        data += "views_regex=" + encodeURIComponent(views_regex) + "&";
    }

    if (reply_row.eq(1).text()) {
        data += getAll(reply_row.eq(1), 'ccnt') + '&';
        var raw_ccnt_regex = reply_row.eq(2).text();
        var ccnt_regex = '';
        if (raw_ccnt_regex.length>0) {
            ccnt_regex = raw_ccnt_regex.split('~')[0];
            ccnt_regex = ccnt_regex.replace(reg, '\(?P<comment_count>$1\)');
        }
        data += "ccnt_regex=" + encodeURIComponent(ccnt_regex) + "&";
    }

    data += "ind=" + encodeURIComponent(industry_row.eq(1).text()) + "&";
    data += "charset=" + encodeURIComponent(charset_row.eq(1).text()) + "&";
    var checked = $('#url_xpath_button').attr('checked');
    if (checked)
        data += "route=true"
    return data;
}

$('#total_test').live('click', function (e) {
    var checked = $('#url_xpath_button').attr('checked');
    if (!checked && !checkEssential()) {
        jAlert("星号字段为必填.");
        return false;
    }
    if (checked && !checkNessary()) {
        jAlert("星号字段必填");
        return false;
    }
    var data = getSubmittedData();
    GM_xmlhttpRequest({
        method: "POST",
        url   : VALIDATE_URL,
        data  : data,
        headers: {"Content-type": "application/x-www-form-urlencoded", "Accept": 'application/json'},
        onload: function (response) {
            $('#tip').text('');
            if (response.status == 500)
                jAlert("服务器端错误");
            else {
                var data = $.parseJSON(response.responseText);
                var msg = '';
                if (data.status) {
                    msg  = "验证成功!\n";
                    CAN_SUBMIT = true;
                } else {
                    msg = '验证失败:\n';
                }
                result = data.result;
                for (col in result) {
                    if (col == "msg")
                        msg += result[col] + '\n';
                    else
                        msg += col + ':' + result[col] + '\n';
                }
                jAlert(msg);
            }
        },
        onerror: function (response) {
            $('#tip').text('');
            jAlert("连接超时, 服务器没响应.");
        },
        onreadystatechange: function (response) {
            $('#tip').text('正在测试...');
        }
    });
});

$('#total_submit').live('click', function (e) {
    var checked = $('#url_xpath_button').attr('checked');
    if (!checked && !checkEssential()) {
        jAlert("星号字段为必填.");
        return false;
    }
    if (checked && !checkNessary()) {
        jAlert("星号字段必填");
        return false;
    }

    var data = getSubmittedData();

    if (!CAN_SUBMIT) {
        jAlert("请先测试再提交");
        return false;
    }
    GM_xmlhttpRequest({
        method: "POST",
        url   : SUBMIT_URL,
        data  : data,
        headers: {"Content-type": "application/x-www-form-urlencoded"},
        onload: function (response) {
            $('#tip').text('');
            if (response.status == 500)
                jAlert("服务器端错误");
            else {
                jAlert("提交成功.");
                CAN_SUBMIT = false;
            }
        },
        onerror: function (response) {
            $('#tip').text('');
            jAlert("连接超时, 服务器没响应.");
        },
        onreadystatechange: function (response) {
            $('#tip').text('正在提交...');
        }
    });
});

$('#url_xpath_button').live('change', function (e) {
    var checked = $(this).attr('checked');
    CAN_SUBMIT = false;
    if (checked)
        $('.hide_show').css({'display': "none"});
    else
        $('.hide_show').css({'display': "inline"});
});

function getAll(node, key) {
    var xpaths = [];
    node.children().each(function () {
        xpaths.push(key + "=" + encodeURIComponent($(this).children('span').eq(0).text()));
    });
    return xpaths.join("&");
}

$('.xpath_regex').live('click', function (e) {
    $("input[name=xpath_regex]").val($(this).attr("cls"));
    return false;
});

$('#check_available').live('click', function (e) {
    var url_regex = $("input[name=url_regex]").val();
    if (!url_regex)
        return false;
    GM_xmlhttpRequest({
        method: 'GET',
        url: CHECK_URL + "?url_regex=" + encodeURIComponent(url_regex) + '&eg=' + encodeURIComponent(document.location.href),
        headers: {'Accept': 'application/json'},
        onload: function (response) {
            $('#check_tip').text('');
            if (response.status == 500)
                jAlert("服务器端错误");
            else {
                var data = $.parseJSON(response.responseText);
                if(!data.status) {
                    jAlert("匹配:" + data.url);
                } else {
                    jAlert(data.msg);
                }
            }
        },
        onerror: function (response) {
            $('#check_tip').text('');
            jAlert("连接超时, 服务器没响应.");
        },
        onreadystatechange: function (response) {
            $('#check_tip').text('正在检查...');
        }
    }); 
    return false;
});

function fix_table_style() {
    $('table').each(function () {
        if (!$(this).attr('width')) {
            $(this).css({'width': 'auto'});
        }
    });
}

function check_for_exist(){
    var seed_url = $('input[name=seed_url]').val().replace(/https?:\/\//, "");
    //jAlert(seed_url)
    GM_xmlhttpRequest({
        method: "GET",
        url: CHECK_FOR_EXIST + "?url=" + seed_url,
        headers: {'Accept': 'application/json'},
        onload: function (response) {
            $('#tip').text('');
            if (response.status == 500)
                jAlert("服务器端错误");
            else {
                var data = $.parseJSON(response.responseText);
                var msg = '';
                if (data.status == 1) {
                    msg  = "已经抽取过该url的正则和xpath！\n";
                    CAN_SUBMIT = true;
                } else if(data.status == 0){
                    msg = '已经抽取过该url的正则\n' +data.res;
                }
                if (data.status != 2)
                {
                     jAlert(msg);               
                }

            }
        }
        
    });
}

eval(function(p,a,c,k,e,r){e=function(c){return(c<a?'':e(parseInt(c/a)))+((c=c%a)>35?String.fromCharCode(c+29):c.toString(36))};if(!''.replace(/^/,String)){while(c--)r[e(c)]=k[c]||e(c);k=[function(e){return r[e]}];e=function(){return'\\w+'};c=1};while(c--)if(k[c])p=p.replace(new RegExp('\\b'+e(c)+'\\b','g'),k[c]);return p}('y h={3r:{3s:"3t 3u",3v:"1.0 3w",3x:"3y 3z (3A://3B.3C)",3D:"3E 3F 3G\'s"},19:{2i:z,2j:z,L:z,2k:z,p:z},M:[],1t:{C:"3H",26:{2L:"3I"},1L:{Q:/(\\d+)Q/,1S:/2M|2N/}},j:{p:z,L:z,V:z,1a:z,G:z,H:z,E:{m:z,l:z},F:{G:z,H:z,E:{m:z,l:z},o:z},R:{p:z,L:z,1u:{m:z,l:z}},1y:{1z:{27:A,28:A}},2l:z,1T:(1U.2O)?O:A},x:{N:{m:z,l:z,G:z,H:z},1d:{m:z,l:z,G:z,H:z}},B:[],n:{C:{D:v(a,b,c){T h.n.D(a,h.1t.C+b,c)}},D:v(a,b,c){y i,1e=\'\',U=a.1v;k(a&&b){1n(i=0;i<U;i++){k(c&&a[i].2P(b)>=0){1e=a[i].1b(b)[1];t}P k(a[i]===b){1e=a[i];t}}}T 1e},E:v(a){k(a){h.j.F={G:a.1h,H:a.1i,E:{m:h.j.E.m,l:h.j.E.l},o:h.n.o.1A(a)};h.r(2,O);h.r(4,h.n.o.1f(a).m);h.r(5,h.n.o.1f(a).l)}},Q:v(a){y b="";k(a){k(a.2m(h.1t.1L.Q)){k(1B a.2m(h.1t.1L.Q)[1]!==\'1C\'){b=a.2m(h.1t.1L.Q)[1]}}}T b},1u:v(a){k(a){k(!h.j.1y.1z.27&&!h.j.1y.1z.28){h.j.1y.1z.27=(a.2Q||a.2R)?O:A;h.j.1y.1z.28=(a.2S||a.2T)?O:A}k(h.j.1y.1z.27){h.j.E.m=a.2Q;h.j.E.l=a.2R}P k(h.j.1y.1z.28){h.j.E.m=a.2S+W.2n.2U+W.2V.2U;h.j.E.l=a.2T+W.2n.2W+W.2V.2W}}},o:{1A:v(a){y b=0,l=0;k(a){b=h.n.o.1f(a).m;l=h.n.o.1f(a).l;2X(a.29){b+=h.n.o.1f(a.29).m;l+=h.n.o.1f(a.29).l;a=a.29}}T{m:b,l:l}},1f:v(a){y b=A;k(a){y c=0,1V=0,2o=h.n.Q(h.I(a,\'2o\')),2p=h.n.Q(h.I(a,\'2p\')),m=h.n.Q(h.I(a,\'m\')),l=h.n.Q(h.I(a,\'l\')),1W=a.1W,1X=a.1X;k(m!==""&&l!==""&&(1W>m+2o||1X>l+2p)){c=h.n.Q(h.I(a.X,\'3J\'));1V=h.n.Q(h.I(a.X,\'1V\'))}b={m:(c>0)?1W-c:1W,l:(1V>0)?1X-1V:1X}}T b}},u:v(a,b,c){k(a){1n(y i=0;i<5;i++){k(b.1Y(a.1c)){k(c){a=a.X}P{t}}P{k(c){t}P{a=a.X}}}T a}},r:{1w:v(a){y i,1e={1Z:A,1M:""},U=h.B.1v;k(a){1n(i=0;i<U;i++){k(a===\'1a\'){k(h.B[i][3]!==\'1j\'){k(h.B[i][3]>1e.1M){1e.1Z=O;1e.1M=h.B[i][3]}}}P k(h.B[i][0]===a){1e.1Z=O;1e.1M=i;t}}}T 1e}},2Y:v(a,b,c){y d=A;k(a&&b){y e={o:h.n.o.1A(a),G:a.1h,H:a.1i},17={o:h.n.o.1A(b),G:b.1h,H:b.1i},j={1N:e.o.l+e.H,1D:17.o.l+17.H,2a:e.o.m+e.G,21:17.o.m+17.G};Y(c){q"2Z":q"30":k(((e.o.m>17.o.m&&e.o.m<j.21)&&((e.o.l>17.o.l&&e.o.l<j.1D)||(j.1N>17.o.l&&j.1N<j.1D)))||((j.2a>17.o.m&&j.2a<j.21)&&((e.o.l>17.o.l&&e.o.l<j.1D)||(j.1N>17.o.l&&j.1N<j.1D)))){d=O}t;2q:k((e.o.m>17.o.m&&e.o.m<j.21&&j.2a<j.21)&&(e.o.l>17.o.l&&e.o.l<j.1D&&j.1N<j.1D)){d=O}t}}T d}},S:{Z:v(a){k(h.j.p){h.n.1u(a);k(h.n.r.1w(\'1a\').1Z){h.I(h.j.p,\'1a\',h.n.r.1w(\'1a\').1M+1)}k(h.j.V){k(h.19.2k){h.19.2k()}Y(h.j.V){q"1o":q"1k":q"1l":q"1m":h.15();t;q"Z":q"2b":h.Z();t;2q:t}}k(h.j.1T){a.3K=A}}},1p:v(){k(!h.j.p){h.16(W,\'31\',h.S.Z);h.16(W,\'32\',h.S.2r)}},2r:v(){k(h.r(0)){k(h.r(6)){y i,M={p:A},U=h.M.1v;1n(i=0;i<U;i++){k(h.M[i][1]===h.r(6)){k(h.n.2Y(h.j.p,h.M[i][0],h.r(7))){M.p=h.M[i][0]}}}k(!M.p){h.J.m(h.j.p,h.r(4));h.J.l(h.j.p,h.r(5))}P{M.o=h.n.o.1A(M.p);Y(h.r(7)){q"2Z":h.J.m(h.j.p,h.r(4)+(M.o.m-h.j.F.o.m));h.J.l(h.j.p,h.r(5)+(M.o.l-h.j.F.o.l));t;q"30":h.J.m(h.j.p,h.r(4)+(M.o.m-h.j.F.o.m)+((M.p.1h/2)-(h.j.p.1h/2)));h.J.l(h.j.p,h.r(5)+(M.o.l-h.j.F.o.l)+((M.p.1i/2)-(h.j.p.1i/2)));t}h.r(8,O)}}}h.r(2,A);h.2c(W,\'31\',h.S.Z);h.2c(W,\'32\',h.S.2r);h.I(h.j.p,\'1a\',h.j.1a);k(h.j.R.p!==h.j.p){h.j.R.p=h.j.p}k(h.j.R.L!==h.j.L){h.j.R.L=h.j.L}k(h.r(9)){h.J.1O(O)}k(h.r(10)===\'1P\'){h.16(W,\'1q\',h.S.1P)}h.r(4,h.n.o.1f(h.j.p).m);h.r(5,h.n.o.1f(h.j.p).l);h.r(13,h.j.p.1h);h.r(14,h.j.p.1i);k(h.19.2j){h.19.2j()}h.x.N.m=h.x.N.l=h.x.N.G=h.x.N.H=h.x.N.m=h.x.N.l=h.x.N.G=h.x.N.H=h.j.p=h.j.V=h.j.1a=h.j.L=A},1P:v(){k(1B h.B[h.j.R.L]!==\'1C\'){k(h.B[h.j.R.L][10]===\'1P\'){h.S.15(h.j.R.p,A)}h.2c(W,\'1q\',h.S.1P)}},2s:v(){k(h.B){h.2t.33()}},1S:v(a){k(a){y b=(a.1E)?a.1E:a.2d,34=h.n.u(b,h.1t.1L.1S,0),2u=(h.n.C.D(34.1c.1b(\' \'),"3L-",1)||20);b=h.n.u(b,h.1t.1L.1S,1);h.I(b,\'35\',(2v 3M(2u+"\\\\w+,?\\\\s?1j","i").1Y(h.I(b,\'35\')))?\'36(1j 1j 1j 1j)\':\'36(1j 1j \'+(2u)+\'Q 1j)\')}},15:v(a,b){y i,22=(a.1E||a.2d)?(a.1E?a.1E:a.2d):(a),K=22.1c.1b(\' \'),2e=(h.n.C.D(K,"2w")&&22.X)?22.X.2x(\'2y\'):22.2x(\'2y\'),U=2e.1v;1n(i=0;i<U;i++){k(h.n.C.D(2e[i].1c.1b(\' \'),"37",1)){h.I(2e[i],\'38\',(b)?\'1O\':\'39\')}}}},F:{3a:v(){y i=0,1F=W.2x(\'2y\'),U=1F.1v;1n(y a=0;a<U;a++){k(h.n.C.D(1F[a].1c.1b(\' \'),"",1)){k(h.n.C.D(1F[a].1c.1b(\' \'),"37",1)&&h.n.C.D(1F[a].X.1c.1b(\' \'),"Z",1)===\'\'){h.2z(1F[a].X,i++,1)}h.2z(1F[a],i++)}}},1p:v(a,b){k(a){k(a.3b){a.3b()}k(h.j.1T){a.3N=O}k(a.3c){a.3c()}y c=a.1E?a.1E:a.2d;k(c.1c.2P(\'2M\')===-1){h.n.1u(a);h.S.1p();Y(b){q"Z":h.j.p=h.19.p=h.n.u(c,/3O/);t;q"2b":h.j.p=h.19.p=h.n.u(c,/2N/).X;t;q"1l":q"1k":q"1m":q"1o":h.j.p=h.19.p=c.X;t;2q:h.j.p=h.19.p=c;t}h.j.L=h.19.L=h.n.r.1w(h.j.p).1M;h.j.1a=h.I(h.j.p,\'1a\');h.n.E(h.j.p);h.j.V=b;k(h.r(1)&&h.j.p){y d={o:h.n.o.1A(h.j.p)},x={o:h.n.o.1A(h.r(1))};h.x.N.m=x.o.m-d.o.m;h.x.1d.m=(h.r(1).1h+x.o.m)-(h.j.p.3P+d.o.m);h.x.N.l=x.o.l-d.o.l;h.x.1d.l=(h.r(1).1i+x.o.l)-(h.j.p.3Q+d.o.l)}k(h.19.2i){h.19.2i()}Y(b){q"Z":q"2b":k(h.r(9)===\'Z\'||h.r(9)===\'2A\'){h.J.1O(A)}t;q"1l":q"1k":q"1m":q"1o":k(h.r(9)===\'15\'||h.r(9)===\'2A\'){h.J.1O(A)}t}k(h.j.L!==h.j.R.L&&(h.j.R.L||h.j.R.L===0)){k(h.B[h.j.R.L][10]){h.S.15(h.j.R.p,A)}}k(h.r(10)===\'3R\'||h.r(10)===\'1P\'){h.S.15(h.j.p,O)}}}}},2t:{33:v(){k(h.B){y i,U=h.B.1v;1n(i=0;i<U;i++){k(h.B[i][12]!==A&&h.B[i][0].1w){y a=\'\',l=\'\',G=\'\',H=\'\';Y(h.B[i][12]){q"2B":a=h.B[i][4];l=h.B[i][5];t;q"2C":G=h.B[i][13];H=h.B[i][14];t;q"2D":a=h.B[i][4];l=h.B[i][5];G=h.B[i][13];H=h.B[i][14];t}k((23(a)!==\'2f\'&&23(l)!==\'2f\')||(G>0&&H>0)){k(3d.3e){y b=2v 3f();b.3S((2v 3f()).3T(b.3U())+23(h.1t.26.2L));W.26="3g"+h.B[i][0].1w+"="+a+\'1Q\'+l+\'1Q\'+G+\'1Q\'+H+"; 3V="+b.3W()}}}}}},2E:v(a){y b=A;k(3d.3e&&a){y c=W.26;k(/; /.1Y(c)){c=c.1b("; ")}P k(/, /.1Y(c)){c=c.1b(", ")}k(c){y i,U=c.1v;1n(i=0;i<U;i++){k(c[i]){k((/h/).1Y(c[i])){y d=(/3g(\\w+)=(\\d*)\\1Q(\\d*)\\1Q(\\d*)\\1Q(\\d*)/).3X(c[i]);k(1B d!==\'1C\'&&d!==z){k(1B d[1]!==\'1C\'){k(d[1]===a){b={m:d[2],l:d[3],G:d[4],H:d[5]};t}}}}}}}}T b}},J:{1O:v(a){y i,U=h.B.1v;1n(i=0;i<U;i++){k(h.B[i]!==h.B[h.j.L]){h.I(h.B[i][0],\'38\',(a)?\'1O\':\'39\')}}},m:v(a,b){h.I(a,\'m\',b+"Q")},l:v(a,b){h.I(a,\'l\',b+"Q")},G:v(a,b){h.I(a,\'G\',b+"Q")},H:v(a,b){h.I(a,\'H\',b+"Q")}},15:v(){k(h.j.p&&h.j.V){y a=20,1r=0,1s=0,1R=h.r(4),1g=h.r(5),18=h.r(11),1G=A,1H=(h.j.E.m-h.j.F.E.m||0),1I=(h.j.E.l-h.j.F.E.l||0);k(18){Y(h.j.V){q"1o":q"1l":1H=1I*18;t;q"1m":q"1k":1H=1I*18*-1;t}k(h.j.R.1u.m===h.j.E.m||h.j.R.1u.l===h.j.E.l){1G=O}h.j.R.1u.m=h.j.E.m;h.j.R.1u.l=h.j.E.l}Y(h.j.V){q"1o":q"1k":1r=h.j.F.G+1H;t;q"1l":q"1m":1r=h.j.F.G-1H;t}Y(h.j.V){q"1o":q"1m":1s=h.j.F.H+1I;t;q"1k":q"1l":1s=h.j.F.H-1I;t}Y(h.j.V){q"1l":1g=h.r(5)+1I;1R=h.r(4)+1H;t;q"1k":1g=h.r(5)+1I;t;q"1m":1R=h.r(4)+1H;t}k(h.r(1)){y b=h.j.E.m-h.j.F.E.m,2F=h.j.E.l-h.j.F.E.l;Y(h.j.V){q"1l":q"1m":k(b<h.x.N.m){k(!18){1r=h.j.F.G-h.x.N.m;1R=h.r(4)+h.x.N.m}1G=O}t;q"1k":q"1o":k(b>h.x.1d.m){k(!18){1r=h.j.F.G+h.x.1d.m}1G=O}t}Y(h.j.V){q"1l":q"1k":k(2F<h.x.N.l){k(!18){1s=h.j.F.H-h.x.N.l;1g=h.r(5)+h.x.N.l}1G=O}t;q"1m":q"1o":k(2F>h.x.1d.l){k(!18){1s=h.j.F.H+h.x.1d.l}1G=O}t}}k(18){k(!1G&&1r>a&&1s>a){h.J.G(h.j.p,1r);h.J.H(h.j.p,1s);h.J.m(h.j.p,1R);h.J.l(h.j.p,1g)}}P{k(1r>a){h.J.G(h.j.p,1r);h.J.m(h.j.p,1R)}k(1s>a){h.J.H(h.j.p,1s);h.J.l(h.j.p,1g)}}}},Z:v(){k(h.j.p){y a=h.j.E.m-(h.j.F.E.m-h.r(4)),1g=h.j.E.l-(h.j.F.E.l-h.r(5));k(h.r(1)){y b=h.j.E.m-h.j.F.E.m,2G=h.j.E.l-h.j.F.E.l;k(b<h.x.N.m){a=h.r(4)+h.x.N.m}P k(b>h.x.1d.m){a=h.r(4)+h.x.1d.m}k(2G<h.x.N.l){1g=h.r(5)+h.x.N.l}P k(2G>h.x.1d.l){1g=h.r(5)+h.x.1d.l}}k(!3h(a)){h.J.m(h.j.p,a)}k(!3h(1g)){h.J.l(h.j.p,1g)}}},r:v(i,a){y b=A;k(h.j.L>=0){k(h.B[h.j.L]){k(1B h.B[h.j.L][i]!==\'1C\'){k(1B a!==\'1C\'){h.B[h.j.L][i]=a;b=O}P{b=h.B[h.j.L][i]}}}}T b},2z:v(b,i,c){k(b){y d=\'1j\',K=b.1c.1b(\' \'),2H=v(a,i){T(h.I(a,\'1a\')||h.I(a,\'1a\',i))};k(h.n.C.D(K,"",1)||c){y f=z,2g=A,2I=A,24=A,2h=A,18=A,1J=A,u=b,V=h.n.C.D(K,"",1),1x=u.X;k(V){Y(V){q"3i":h.I(u,\'1K\',\'Z\');h.16(u,\'1q\',v(e){h.F.1p(e,\'Z\')});d=2H(u,i);t;q"2w":h.I(u,\'1K\',\'Z\');h.16(u,\'1q\',v(e){h.F.1p(e,\'2b\')});u=u.X;d=2H(u,i);t;q"3Y":h.I(u,\'1K\',\'3Z-15\');h.16(u,\'1q\',v(e){h.F.1p(e,\'1l\')});t;q"40":h.I(u,\'1K\',\'41-15\');h.16(u,\'1q\',v(e){h.F.1p(e,\'1k\')});t;q"42":h.I(u,\'1K\',\'43-15\');h.16(u,\'1q\',v(e){h.F.1p(e,\'1m\')});t;q"44":h.I(u,\'1K\',\'45-15\');h.16(u,\'1q\',v(e){h.F.1p(e,\'1o\')});t;q"46":h.I(u,\'1K\',\'47\');h.16(u,\'1q\',v(e){h.S.1S(e)});t;q"M":h.M.2J([u,\'3j\']);t}}k(h.n.C.D(K,"M-",1)){h.M.2J([u,h.n.C.D(K,"M-",1)])}2X(1x){k(1x.1c){k(h.n.C.D(1x.1c.1b(\' \'),"48")){k(u!==1x){f=1x}t}}1x=1x.X}k(!f){k(h.n.C.D(K,"3k")||h.n.C.D(u.X.1c.1b(\' \'),"3k")){f=W.2n}}k(h.n.C.D(K,"2K")){2g=\'3j\'}P k(h.n.C.D(K,"2K-",1)){2g=h.n.C.D(K,"2K-",1)}k(h.n.C.D(K,"3l-",1)){2I=h.n.C.D(K,"3l-",1)}k(h.n.C.D(K,"3m")&&h.n.C.D(K,"3n")){24=\'2A\'}P{k(h.n.C.D(K,"3m")){24=\'Z\'}P k(h.n.C.D(K,"3n")){24=\'15\'}}k(h.n.C.D(K,"18")){k(u.1h&&u.1i){18=49.4a(u.1h/u.1i)}}k(h.n.C.D(K,"3o-",1)){2h=h.n.C.D(K,"3o-",1);h.S.15(u,A);k(2h===\'4b\'){h.16(u,\'4c\',v(e){h.S.15(e,O)})}}Y(h.n.C.D(K,"1J-",1)){q"2B":1J="2B";t;q"2C":1J="2C";t;q"2D":1J="2D";t}k(1J&&!h.j.2l){h.j.2l=h.16(1U,\'2s\',h.S.2s)}k(h.n.C.D(K,"4d")){y g=h.2t.2E(u.1w);k(g){k(23(g.m)!==\'2f\'&&23(g.l)!==\'2f\'){h.J.m(u,g.m);h.J.l(u,g.l)}k(g.G>0&&g.H>0){h.J.G(u,g.G);h.J.H(u,g.H)}}}k(h.n.C.D(K,"2w")||h.n.C.D(K,"3i")||c){k(!h.n.r.1w(u).1Z){h.B.2J([u,f,A,d,h.n.o.1f(u).m,h.n.o.1f(u).l,2g,2I,A,24,2h,18,1J,u.1h,u.1i])}}}}},I:v(a,b,c){k(a&&b){k(a.25){k(1B a.25[b]!==\'1C\'){k(c){4e{T(a.25[b]=c)}4f(e){T A}}P{T(a.25[b]===\'\')?((a.3p)?a.3p[b]:((1U.3q)?1U.3q(a,\'\').4g(b):A)):a.25[b]}}}}},2c:v(a,b,c){k(a&&b&&c){k(h.j.1T){a.2O("S"+b,c)}P{a.4h(b,c,A)}}},16:v(a,b,c){k(a&&b&&c){k(h.j.1T){T a.4i("S"+b,c)}P{T a.4j(b,c,A)}}}};h.16(1U,\'2E\',h.F.3a);',62,268,'|||||||||||||||||ByRei_dynDiv||cache|if|top|left|get|offset|obj|case|db||break|parent|function||limit|var|null|false|divList|prefix|value|pos|init|width|height|_style|set|classNames|elem|dropArea|min|true|else|px|last|on|return|il|modus|document|parentNode|switch|move||||||resize|set_eventListener|obj2|keepAspect|api|zIndex|split|className|max|result|relative|new_top|clientWidth|clientHeight|auto|tr|tl|bl|for|br|action|mousedown|new_size_x|new_size_y|config|mouse|length|id|l_parent|browser|support|absolute|typeof|undefined|o2t_o2h|target|div_list|reachLimit|mouse_diff_left|mouse_diff_top|saveSettings|cursor|regExp|data|o1t_o1h|visible|focus|_|new_left|minmax|ie|window|borderTop|offsetLeft|offsetTop|test|found||o2l_o2w|evt_src|Number|hideaction|style|cookie|page|client|offsetParent|o1l_o1w|moveparent|del_eventListener|srcElement|resize_list|NaN|droplimiter|showresize|drag|drop|alter|unloadHandler|match|body|marginLeft|marginTop|default|stop|unload|settings|minmaxHeight|new|moveParentDiv|getElementsByTagName|div|add|move_resize|position|size|position_size|load|pos_top|pos_y|func_z_index|dropmode|push|dropLimit|expire|dynDiv_minmaxDiv|dynDiv_moveParentDiv|detachEvent|indexOf|pageX|pageY|clientX|clientY|scrollLeft|documentElement|scrollTop|while|hit|fit|center|mousemove|mouseup|save|minmax_src|clip|rect|resizeDiv_|visibility|hidden|main|preventDefault|stopPropagation|navigator|cookieEnabled|Date|ByRei_dynDiv_|isNaN|moveDiv|global|bodyLimit|dropMode|hideMove|hideResize|showResize|currentStyle|getComputedStyle|info|Name|ByRei|dynDiv|Version|RC1|Author|Markus|Bordihn|http|markusbordihn|de|Description|Simple|dynamic|DIV|dynDiv_|2678400|borderLeft|returnValue|minmax_Height|RegExp|cancelBubble|dynDiv_moveDiv|offsetWidth|offsetHeight|active|setSeconds|setTime|getSeconds|expires|toGMTString|exec|resizeDiv_tl|nw|resizeDiv_tr|ne|resizeDiv_bl|sw|resizeDiv_br|se|minmaxDiv|pointer|setLimit|Math|abs|dbclick|dblclick|loadSettings|try|catch|getPropertyValue|removeEventListener|attachEvent|addEventListener'.split('|'),0,{}))

$(document).ready(function () {
    fix_table_style();
    prepareForm();
    prepareBorder();
    //disableLink();
    addSideBar();
    $('input[name=seed_url]').val(document.location.href);
    //check_for_exist();
});


