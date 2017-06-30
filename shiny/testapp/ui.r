library(shiny)
library(shinythemes)
library(googleVis)
library(ggvis)

shinyUI(navbarPage('TAITRA 產品別出口目標市場篩選系統',
  theme = shinytheme('slate'),
  
  tabPanel(strong('選產品'),
           icon = icon('briefcase'),
    
    # titlePanel(),
    
    sidebarLayout(
      
      sidebarPanel(
        width = 3,
        uiOutput('ctrySelector'),
        selectInput('myCtry', h5(strong('選擇進口國'), style = 'color:#FFFFFF'), choices = c('中國大陸', '中非', '丹麥', '亞塞拜然', '亞美尼亞', '以色列', '俄羅斯', '保加利亞', '克羅埃西亞', '冰島', '加拿大', '匈牙利', '南非', '南韓', '卡達', '印尼', '印度', '厄瓜多', '哈薩克', '哥倫比亞', '哥斯大黎加', '喀麥隆', '喬治亞', '土耳其', '坦尚尼亞', '埃及', '塞內加爾', '塞席爾', '塞爾維亞', '墨西哥', '多哥', '多明尼加', '大溪地', '奧地利', '安哥拉', '安地卡', '尚比亞', '尼加拉瓜', '尼日', '尼泊爾', '巴勒斯坦', '巴哈馬', '巴基斯坦', '巴拉圭', '巴拿馬', '巴林', '巴西', '巴貝多', '布吉納法索', '希臘', '帛琉', '幾內亞', '德國', '愛沙尼亞', '愛爾蘭', '拉脫維亞', '挪威', '捷克', '摩洛哥', '摩爾多瓦', '斐濟', '斯洛伐克', '斯洛維尼亞', '斯里蘭卡', '新克里多尼亞', '新加坡', '日本', '智利', '柬埔寨', '格陵蘭', '模里西斯', '比利時', '汶萊', '沙烏地阿拉伯', '法國', '波士尼亞赫塞哥維納', '波札那', '波蘭', '泰國', '澳大利亞', '澳門', '烏克蘭', '烏干達', '烏拉圭', '牙買加', '獅子山', '玻利維亞', '瑞典', '瑞士', '瓜地馬拉', '白俄羅斯', '百慕達', '盧安達', '盧森堡', '科威特', '秘魯', '突尼西亞', '立陶宛', '約旦', '紐西蘭', '索羅門群島', '維德角', '羅馬尼亞', '美國', '義大利', '聖多美普林西比', '芬蘭', '英國', '荷蘭', '莫三比克', '菲律賓', '葉門', '葡萄牙', '蒙古', '蒙特內哥羅共和國', '蒲隆地', '蓋亞那', '薩摩亞', '薩爾瓦多', '衣索比亞', '西班牙', '象牙海岸', '貝南', '貝里斯', '賽普勒斯', '越南', '辛巴威', '阿富汗', '阿拉伯聯合大公國', '阿曼', '阿根廷', '阿爾及利亞', '阿爾巴尼亞', '阿魯巴', '香港', '馬來西亞', '馬其頓', '馬拉威', '馬爾他', '馬爾地夫', '馬達加斯加'),
                    selected = '日本'),
        HTML('<font color=#C8C8C8>將滑鼠游標移至點上即可顯示產品進口情形。越接近右上角金色邊界之產品，自全球進口表現越佳。</font>')
      ),
      mainPanel(
        h3(strong(textOutput('ctry_title')), style = 'color:#FFFFFF', align = 'center'),
        h4(strong('2015 年自全球進口所有 HS 6 碼產品'), style = 'color:#FFFFFF', align = 'center'),
        div(ggvisOutput('ctry_plot')),
        h6('資料來源：UN Comtrade (2012-2016)', align = 'right'),
        # Copyright notice
        p('Copyright 2017, Taiwan External Trade Development Council', align = 'center')
      )
      
    )
  ),
  
  tabPanel(strong('選市場'),
           icon = icon('plane'),
           
    # titlePanel(),
    
    sidebarLayout(
      
      sidebarPanel(
        width = 3,
        # Choose product of interest
        h5(strong('Step 1: 選擇出口產品'), style = 'color:#FFFFFF'),
        uiOutput('hs2Selector'),
        uiOutput('hs4Selector'),
        uiOutput('hs6Selector'),
        # Choose filtering conditions
        checkboxGroupInput('macro_criteria', label = h5(strong('Step 2: 選擇市場篩選條件'), style = 'color:#FFFFFF'),
                           choices = list('高進口需求' = 1, '整體進口正成長' = 2, '進口來源國數小於平均數' = 3, '有自臺進口' = 4),
                           selected = NULL),
        # Additional Taiwan-related conditions
        conditionalPanel(condition = ('input.macro_criteria.includes("4")'),
                         checkboxGroupInput('tw_criteria', label = '更多臺灣相關篩選條件：',
                                            choices = list('高自臺進口額' = 5, '自臺進口成長率優於整體' = 6, '臺灣市占率高' = 7, '臺灣排名前三' = 8, '主要競爭對手未列前三名' = 9),
                                            selected = NULL)
        )
      ),
      
      mainPanel(
        tags$style(type = 'text/css',
                   # Suppress error messages from reactive functions before output is ready
                   '.shiny-output-error {visibility: hidden;}',
                   '.shiny-output-error:before {visibility: hidden;}',
                   # App title
                   'h2 {color:white; font-weight:bold;}',
                   # Competitors table
                   '#competitors_tbl th {color:white;}',
                   # Filtered table
                   'table.google-visualization-table-table td:nth-child(6) {text-align: center;}',
                   # Specify gvisTable text and background colors
                   '.myTableHeadRow {color:black; background-color:lightgray;} .myTableRow {color:black;} .myOddTableRow {color:black; background-color:#F8F8F8}',
                   # App header
                   'span.navbar-brand {font-weight:bold;}'
        ),
        width = 9,
        tabsetPanel(
          tabPanel('全球總覽',
            # Title
            h3(strong(htmlOutput('p_code')), align = 'center'),
            h5(strong(htmlOutput('p_desc2')), align = 'center'),
            h4(strong(htmlOutput('p_desc4')), align = 'center'),
            h3(strong(htmlOutput('p_desc6')), align = 'center'),
            hr(),
            # Summary statistics
            h4(strong('2015 年全球進口情勢摘要'), style = 'color:#FFFFFF'),
            p('1. 全球進口國家數：', strong(textOutput('p.ncountry', inline = T)), '國。平均進口額', strong(textOutput('p.avg.val', inline = T)), '美元。'),
            p('2. 自臺進口國家數：', strong(textOutput('p_ncountry_tw', inline = T)), '國。平均進口額', strong(textOutput('p.avg.val.tw', inline = T)), '美元。臺灣平均市占率', strong(textOutput('p.avg.share.tw', inline = T)), '%，平均排名第', strong(textOutput('p.avg.rank.tw', inline = T)), '位。'),
            p('3. 自臺進口成長率優於該國整體成長率的共有', strong(textOutput('p.noutperform', inline = T)), '國，占', strong(textOutput('p.outperform.ratio', inline = T)), '%。'),
            p('4. 每一國平均進口來源國數：', strong(textOutput('p.avg.npartner', inline = T)), '國。屬', strong(htmlOutput('p.comp', inline = T)), '度競爭產品。'),
            conditionalPanel(
              condition = ('output.p_ncountry_tw > 0'),
              p('5. 有自臺進口的國家中，臺灣最常面對的競爭對手依序為：'),
              tableOutput('competitors_tbl'),
              p('6. 2015 年臺灣出口商數（*註）：', strong(textOutput('p_nexporter', inline = T)), '家。近三年（2014-2016）有參加貿協拓銷活動者共有', strong(textOutput('p_npar', inline = T)), '家，參與率', strong(textOutput('p_par_rate', inline = T)), '%。')
            ),
            br(),
            h6(em('*註：僅列計對單一國家該項產品年出口額逾 10 萬美元之廠商。')),
            hr(),
            # Filtered table
            h3(strong('【市場篩選結果】'), align = 'center', style = 'color:#A50026'),
            h4(strong('共有', htmlOutput('n_filtered', inline = T), '個市場符合篩選條件：'), align = 'center', style = 'color:#FFFFFF'),
            htmlOutput('p.table'),
            h6('資料來源：UN Comtrade、貿易局、TAITRA CRM (2012-2016)', align = 'right'),
            # Copyright notice
            p('Copyright 2017, Taiwan External Trade Development Council', align = 'center')
          ), 
          tabPanel('個別國家',
                   br(),
                   '功能開發中'
          )
        )
      )
    )
  )
))