library(shiny)
library(readr)
library(stringr)
library(dplyr)
library(data.table)
library(memisc)
library(xtable)
library(ggplot2)
library(ggvis)
library(googleVis)
library(RColorBrewer)

shinyServer(function(input, output, session) {
  
  ###### MODULE A: By Importer ######
  
  ###### A-1: Reading Data ######
  
  # ctry_list <- read_csv('data/country_list.csv',
  #                       locale=locale(encoding='Big5'), col_names = F)[[1]] %>% as.list()
  # # Generate country selection box
  # output$ctrySelector <- renderUI({selectInput('myCtry', '選擇進口國', ctry_list, selected = '日本')})
  
  ctry_tbl <- read_csv('data/country_list.csv',
                       locale=locale(encoding='Big5'), col_types = 'cc')
  ctry_map <- ctry_tbl[['iso']]
  names(ctry_map) <- ctry_tbl[['name']]
  
  output$ctry_title <- renderText({input$myCtry})
  ctry_selected <- reactive({ctry_map[[input$myCtry]]})
  ctry_df <- reactive({
    validate(need(ctry_selected(), ''));
    df <- read_csv(paste0('data/bycountry_', ctry_selected(), '.csv'),
                   locale = locale(encoding = 'Big5'),
                   col_types = paste0(c(rep('c', '4'), rep('d', 6), rep('cddd', 3), 'dc', rep('d', 4)), collapse = ''))
    df$tw_is_ex <- as.logical(df$tw_is_ex)
    df$share_int <- factor(df$share_int, levels = c('0', '(0, 12.5]', '(12.5, 25]', '(25, 37.5]', '(37.5, 50]', '(50, 100]'), ordered = T)
    df <- df[!is.na(df$log_g15), ]
    df[is.na(df$tw_val15), 'tw_val15'] <- 0
    df[is.na(df$tw_share), 'tw_share'] <- 0
    # Artificial data for horizontal line
    df['y'] <- 0
    # Tooltip key
    df$id <- 1:nrow(df)
    df
  })

  # Border data
  b_c <- reactive({
    df <- ctry_df()
    df_ord <- arrange(df[df$g15 >= 0, ], desc(log_val15))
    df_ord$cummax <- cummax(df_ord$log_g15)
    borders <- df_ord[df_ord$log_g15 == df_ord$cummax, c('log_val15', 'log_g15')]
    connectors <- data.frame(log_val15 = borders$log_val15, log_g15 = lag(borders$log_g15))[-1, ]
    b_c <- rbind(borders, connectors) %>% arrange(log_val15)
    b_c
  })
  
  ###### A-2: Plotting ######
  
  # colors
  clr_range <- colorRampPalette(c('#3BB3AE', '#FEF4CF', '#D53F76'), interpolate = 'spline')
  clrs <- c('grey', clr_range(5))
  
  ellipsis <- function(x, max_len = 10) {
    ifelse(nchar(x) <= max_len, x, paste(substr(x, 1, max_len), '..'))
  }
  mark_red <- function(x) {
    ifelse(grepl('-[0-9]+', x), paste0('<font color="red">', x, '</font>'), x)
  }
  round_big <- function(x) {
    ifelse(is.na(x), '-', format(round(x, 2), big.mark = ','))
  }
  allValues <- function(x) {
    if (is.null(x)) return(NULL)
    dat <- ctry_df()
    row <- dat[dat$id == x$id, ]
    paste0('<div style="color:#272B30; line-height:90%"><div align="center"><b><font size=+1 color=#08306B>', row[['product']], '</font>',
           '<br/><font size=-2 color=#08306B>', ellipsis(row[['desc2']]), '</font>',
           '<br/><font size=-2 color=#2171B5>', ellipsis(row[['desc4']]), '</font>',
           '<br/><div style="color:#6BAED6; line-height:150%">', ellipsis(row[['desc6']]), '</div></b></div>',
           '<br/><font size=-2>- 自全球進口額： <b>', round_big(row[['val15']]), '</b> 美元',
           '<br/>- 自全球進口成長率： <b>', mark_red(round_big(row[['g15']])), '</b> %',
           '<br/>- 臺灣市占率： <b>', round(row[['tw_share']], 2), '</b> %',
           '<br/><br/><div align="center"><b>前三大進口來源國及成長率</b></div>',
           '　　　1. ', row[['1_name']], '： <b>', mark_red(round_big(row[['1_g15']])), '</b> %',
           '<br/>　　　2. ', row[['2_name']], '： <b>', mark_red(round_big(row[['2_g15']])), '</b> %',
           '<br/>　　　3. ', row[['3_name']], '： <b>', mark_red(round_big(row[['3_g15']])), '</b> %</font></div>'
           )
  }
  
  ctry_viz <- reactive({
    ggvis(ctry_df()) %>%
      layer_paths(data=b_c(), x = ~log_val15, y = ~log_g15, stroke := '#ffd700',
                  strokeDash := 2, strokeWidth := 1.5) %>%
      layer_points(~log_val15, ~log_g15,
                   shape = ~factor(tw_is_ex),
                   size = ~tw_val15,
                   size.hover := 250,
                   fill = ~factor(share_int),
                   opacity = ~tw_share,
                   opacity.hover := 1,
                   stroke = ~factor(share_int),
                   stroke.hover := 'white',
                   strokeWidth := 2,
                   key := ~id) %>%
      scale_logical('shape', range = c('cross', 'circle')) %>%
      scale_numeric('size', range = c(40, 200)) %>%
      scale_ordinal('fill', range = clrs,
                    domain = c('0', '(0, 12.5]', '(12.5, 25]', '(25, 37.5]', '(37.5, 50]', '(50, 100]')) %>%
      scale_numeric('opacity', domain=c(0, 20), range = c(0.2, 0.9)) %>%
      scale_ordinal('stroke', range = clrs) %>%
      add_axis('x', title='log(自全球進口額)',
               properties = axis_props(title = list(fontSize = 16, fill = 'white'),
                                       labels = list(fill = 'white'),
                                       axis = list(stroke = 'white', strokeWidth = 2),
                                       tick = list(stroke = 'white'))) %>%
      add_axis('y', title='log(自全球進口成長率 + c)',
               properties = axis_props(title = list(fontSize = 16, fill = 'white'),
                                       labels = list(fill = 'white'),
                                       axis = list(stroke = 'white', strokeWidth = 2),
                                       tick = list(stroke = 'white'))) %>%
      hide_legend('size') %>%
      hide_legend('opacity') %>%
      hide_legend('stroke') %>%
      add_relative_scales() %>%  # For relative positioning
      add_legend('fill', title = paste0('臺灣於', input$myCtry, '市占率'),
                 values = c('0 %', '0 - 12.5 %', '12.5 - 25 %', '25 - 37.5 %',
                            '37.5 - 50 %', '逾 50 %'),
                 properties = legend_props(title = list(fontSize = 12, fontWeight = 'bold', fill = '#555555'),
                                           labels = list(fontSize = 11, fontWeight = 'bold', fill = '#555555', dx = 5),
                                           symbol = list(size = 70, strokeWidth = 0),
                                           legend = list(y = scaled_value('y_rel', 0.85)))) %>%
      add_legend('shape', title = '臺灣有無出口', values = c('無', '有'),
                 properties = legend_props(title = list(fontSize = 12, fontWeight = 'bold', fill = '#555555'),
                                           labels = list(fontSize = 11, fontWeight = 'bold', fill = '#555555', dx = 5),
                                           symbol = list(size = 70, strokeWidth = 1.5),
                                           legend = list(y = scaled_value('y_rel', 1)))) %>%
      add_tooltip(allValues, 'hover') %>%
      # workaround to prevent legend from disappearing when using tooltip
      set_options(width = 'auto', height = 'auto', duration = 0, resizable = T)
  })
  ctry_viz %>% bind_shiny('ctry_plot')
  
  ###### MODULE B: By Product ######
  
  ###### B-1: Reading Data ######
  
  # Read HS code table
  hs_tbl <- read_csv('data/hs_table.csv', locale=locale(encoding='Big5'))
  # Remove products without desc2
  hs_tbl <- hs_tbl[!is.na(hs_tbl$desc2), ]

  # Generate HS2 selection box
  hs2s <- unique(paste(substr(hs_tbl$product, 1, 2), '-', substr(hs_tbl$desc2, 1, 16), ifelse(nchar(hs_tbl$desc2) <= 16, '', '..'))) %>% sort()
  output$hs2Selector <- renderUI({selectInput('myhs2', '2碼', as.list(hs2s))})
  # Get HS2 and generate HS4 selection box
  hs2 <- reactive({substr(input$myhs2, 1, 2)})
  hs4s <- reactive({
    subset <- hs_tbl[substr(hs_tbl$product, 1, 2) == hs2(), ]
    unique(paste(substr(subset$product, 1, 4), '-', substr(subset$desc4, 1, 15), ifelse(nchar(subset$desc4) <= 15, '', '..'))) %>% sort()
  })
  output$hs4Selector <- renderUI({selectInput('myhs4', '4碼', as.list(hs4s()))})
  # Get HS4 and generate HS6 selection box
  hs4 <- reactive({substr(input$myhs4, 1, 4)})
  hs4.p <- reactive({
    subset <- hs_tbl[substr(hs_tbl$product, 1, 4) == hs4(), ]
    unique(paste(subset$product, '-', substr(subset$desc6, 1, 14), ifelse(nchar(subset$desc6) <= 14, '', '..'))) %>% sort()
  })
  output$hs6Selector <- renderUI({selectInput('myhs6', '6碼', as.list(hs4.p()))})
  # Get HS6
  p.code <- reactive({substr(input$myhs6, 1, 6)})
  output$p_code <- renderText({paste0('<font color=\"#08306B\"><b>', p.code(), '</b></font>')})
  
  # Read HS2 data
  all.p <- reactive({
    validate(need(hs2(), ''));
    read_csv(paste0('data/comp_aggregate_6_', hs2(), '.csv'), locale = locale(encoding = 'Big5'),
             col_types = paste0(c(rep('c', '5'), rep('d', 15), rep(c('c', rep('d', 5)), 3)), collapse = ''))
  })
  # Extract HS6 data
  p.data <- reactive({
    all.p()[all.p()$product == p.code(), ] %>%
      mutate(outperform = ifelse(tw_g15 >= g15, 'Y', 'N'),
             # To use ICU format, divide percent (tw_share and g15) by 100
             tw_share = tw_share / 100,
             # Because gvisTable doesn't accept Inf, replace all Inf's in growth rate with NA
             g15 = ifelse(is.infinite(g15), NA, g15 / 100)) %>%
      dplyr::select(country, val15, tw_val15, tw_share, g15, outperform, n_partner, tw_rank,
             `1_name`, `2_name`, `3_name`, n_exporter, is_par) %>%
      filter(val15 != 0 & !is.na(val15)) %>%
      setattr('names',
              c('進口國', '進口額(美元)', '自臺進口額(美元)', '臺灣市占率', '整體進口成長率',
                '自臺進口成長率優於整體', '進口來源國數', '臺灣排名',
                '領先國家1', '領先國家2', '領先國家3', '出口商數*', '參加拓銷*')) %>%
      arrange(desc(`自臺進口額(美元)`), desc(自臺進口成長率優於整體), desc(`進口額(美元)`))
  })

  ###### B-2: Summary Statistics ######
  
  # Get HS2, HS4, HS6 names
  p.row <- reactive({all.p()[match(p.code(), all.p()$product), ]})
  desc2_evt <- eventReactive(input$myhs6, {validate(need(hs2(), '')); paste0('<font color=\"#08306B\"><b>', p.row()$desc2, '</b></font>')})
  desc4_evt <- eventReactive(input$myhs6, {validate(need(hs2(), '')); paste0('<font color=\"#2171B5\"><b>', p.row()$desc4, '</b></font>')})
  desc6_evt <- eventReactive(input$myhs6, {validate(need(hs2(), '')); paste0('<font color=\"#6BAED6\"><b>', p.row()$desc6, '</b></font>')})
  output$p_desc2 <- renderText({desc2_evt()})
  output$p_desc4 <- renderText({desc4_evt()})
  output$p_desc6 <- renderText({desc6_evt()})

  # Compute column means
  p.stats <- reactive({
    colMeans(p.data()[c('進口額(美元)', '自臺進口額(美元)', '臺灣市占率',
                        '整體進口成長率', '進口來源國數', '臺灣排名')], na.rm = TRUE)
  })

  # Helper function to format strings
  formatNumber <- function(x, digits = 2) {
    x <- format(round(x, digits), big.mark = ',')
    gsub('[ ]+', '', x)
  }
  
  # Compute summary statistics
  ## No. of countries importing the product
  output$p.ncountry <- renderText({
    nrow(p.data()[p.data()$`進口額(美元)` != 0 & !is.na(p.data()$`進口額(美元)`), ])
  })
  ## Average import value
  output$p.avg.val <- renderText({
    x <- p.stats()[['進口額(美元)']] %>% formatNumber(2)
    ifelse(x == 'NaN', '-', x)
  })
  ## No. of countries importing the product from Taiwan
  output$p_ncountry_tw <- renderText({
    nrow(p.data()[p.data()$`自臺進口額(美元)` != 0 & !is.na(p.data()$`自臺進口額(美元)`), ])
  })
  ## Average import value from Taiwan
  output$p.avg.val.tw <- renderText({
    x <- p.stats()[['自臺進口額(美元)']] %>% formatNumber(2)
    ifelse(x == 'NaN', '-', x)
  })
  ## Average market share of Taiwan
  output$p.avg.share.tw <- renderText({
    x <- (p.stats()[['臺灣市占率']] * 100) %>% formatNumber(2)
    ifelse(x == 'NaN', '-', x)
  })
  ## Average rank of Taiwan
  output$p.avg.rank.tw <- renderText({
    x <- p.stats()[['臺灣排名']] %>% formatNumber(0)
    ifelse(x == 'NaN', '-', x)
  })
  ## No. of countries where growth in imports from Taiwan outperforms overall growth
  output$p.noutperform <- renderText({sum(p.data()$自臺進口成長率優於整體 == 'Y', na.rm = TRUE)})
  ## Ratio of countries where growth in imports from Taiwan outperforms overall growth
  output$p.outperform.ratio <- renderText({
    x <- round(sum(p.data()$自臺進口成長率優於整體 == 'Y', na.rm = TRUE) / nrow(p.data()[p.data()$`自臺進口額(美元)` != 0 & !is.na(p.data()$`自臺進口額(美元)`), ]) * 100, 2)
    ifelse(x == 'NaN', '-', x)
  })
  ## Average number of partners
  output$p.avg.npartner <- renderText({
    x <- p.stats()[['進口來源國數']] %>% formatNumber(0)
    ifelse(x == 'NaN', '-', x)
  })

  # Level of competition
  ## Calculate mean and std of number of partners
  # n_partner.mean <- read_csv('C:/Users/2093/Documents/R/testapp/data/comp_aggregate_6.csv', locale = locale(encoding = 'Big5'),
  #                            col_types = paste0(c(rep('c', '5'), rep('d', 12), rep(c('c', rep('d', 5)), 3)), collapse = '')) %>%
  #   group_by(product) %>%
  #   summarise(p.mean = mean(n_partner, na.rm = T)) %>% `[[`('p.mean') %>%
  #   `^`(1/5) %>% mean(na.rm = T)
  # save(n_partner.mean, file = 'n_partner_mean.RData')
  # n_partner.sd <- read_csv('C:/Users/2093/Documents/R/testapp/data/comp_aggregate_6.csv', locale = locale(encoding = 'Big5'),
  #                          col_types = paste0(c(rep('c', '5'), rep('d', 12), rep(c('c', rep('d', 5)), 3)), collapse = '')) %>%
  #   group_by(product) %>%
  #   summarise(p.mean = mean(n_partner, na.rm = T)) %>% `[[`('p.mean') %>%
  #   `^`(1/5) %>% sd(na.rm = T)
  # save(n_partner.sd, file = 'n_partner_sd.RData')
  load('data/n_partner_mean.RData')
  load('data/n_partner_sd.RData')
  ## Convert number of partners to z-score
  n_partner.zscore <- reactive({
    (`^`(p.stats()[['進口來源國數']], 1/5) - n_partner.mean) / n_partner.sd
  })
  ## Map to level of competition
  output$p.comp <- renderText({
    paste(
      # Use 9301 to test
      ifelse(is.na(n_partner.zscore()), '-',
        cases(
          #n_partner.zscore() <= -3 -> '<font color=\"#1A9850\"><b>極低',
          #n_partner.zscore() > -3 & n_partner.zscore() <= -2 -> '<font color=\"#1A9850\"><b>低',
          n_partner.zscore() <= -2 -> '<font color=\"#1A9850\"><b>低',
          n_partner.zscore() > -2 & n_partner.zscore() <= -1 -> '<font color=\"#66BD63\"><b>中低',
          n_partner.zscore() > -1 & n_partner.zscore() < 1 -> '<font color=\"#FDAE61\"><b>中',
          n_partner.zscore() >= 1 & n_partner.zscore() < 2 -> '<font color=\"#D73027\"><b>中高',
          n_partner.zscore() >= 2 -> '<font color=\"#A50026\"><b>高'
          #n_partner.zscore() >= 2 & n_partner.zscore() < 3 -> '<font color=\"#A50026\"><b>高'
          #n_partner.zscore() >= 3 -> '<font color=\"#A50026\"><b>極高'
        )
      ), '</b></font>')
  })
  
  # Top 3 competitors
  ## Filter for countries importing from Taiwan
  p.data.tw <- reactive({p.data()[!is.na(p.data()['臺灣排名']), ]})
  ## Extract all top three's and build contingency table
  competitors <- reactive({
    cp <- c(p.data.tw()$領先國家1, p.data.tw()$領先國家2, p.data.tw()$領先國家3) %>%
      table() %>% sort(decreasing = T)
    cp[(names(cp) != '臺灣') & (names(cp) != '-')]
  })
  ## Get no. of competitors
  n_competitors <- reactive({min(length(competitors()), 3)})
  ## Buffer to prevent warning raised by data.frame() during invalidation
  comp.list <- reactive({
    ls <- list()
    ls[['排名']] <- 1:n_competitors()
    ls[['國家']] <- names(competitors()[1:n_competitors()])
    ls[['進入各國進口國前3名次數']] <- as.vector(competitors()[1:n_competitors()])
    ls
  })
  ## Output table
  output$competitors_tbl <- renderTable({data.frame(comp.list())})
  
  # No. of Taiwan exporters by commodity
  n_com_p <- read_csv('data/n_com_p.csv')
  n_com_p$product <- str_pad(n_com_p$product, 6, 'left', '0')
  n_com_row <- reactive({n_com_p[n_com_p$product == p.code(), ]})
  output$p_nexporter <- renderText({
    x <- n_com_row()$n_exporter
    ifelse(length(x) == 0, 0, x %>% formatNumber(0))
  })
  output$p_npar <- renderText({
    x <- n_com_row()$is_par
    ifelse(length(x) == 0, 0, x %>% formatNumber(0))
  })
  output$p_par_rate <- renderText({
    x <- n_com_row()$par_rate
    ifelse(length(x) == 0, '-', x %>% formatNumber(2))
  })
  
  ###### B-3: Filtered Table ######

  # List of conditions
  conditions <- reactive({
    list(
      as.vector(scale(p.data()$`進口額(美元)`)) >= 1,
      p.data()$整體進口成長率 > 0,
      p.data()$進口來源國數 < as.integer(p.stats()[['進口來源國數']]),
      !is.na(p.data()$臺灣排名),
      as.vector(scale(p.data()$`自臺進口額(美元)`)) >= 1,
      p.data()$自臺進口成長率優於整體 == 'Y',
      as.vector(scale(p.data()$臺灣市占率)) >= 1,
      p.data()$臺灣排名 <= 3,
      (!p.data()$`領先國家1` %in% names(competitors()[1:n_competitors()])) & (!p.data()$`領先國家2` %in% names(competitors()[1:n_competitors()])) & (!p.data()$`領先國家3` %in% names(competitors()[1:n_competitors()])),
      # default condition
      rep(T, nrow(p.data()))
    )
  })
  # Filter table based on selected conditions
  p.filtered <- reactive({
    dt <- p.data()[Reduce(`&`, conditions()[as.integer(c(input$tw_criteria, input$macro_criteria, 10))]), ]
    # Remove empty rows
    dt[!is.na(dt$進口國), ]
  })
  # No. of countries filtered
  output$n_filtered <- renderText({
    paste0('<font color=\"#D73027\"><b>', nrow(p.filtered()), '</b></font>')
  })
  # Output googleVis table
  output$p.table <- renderGvis({
    p.filtered() %>%
      gvisTable(formats = list('進口額(美元)' = '#,###',
                               '自臺進口額(美元)' = '#,###',
                               '臺灣市占率' = '#.##%',
                               '整體進口成長率' = '#.##%'),
                options = list(height = 'automatic', page = 'enable', pageSize = 10,
                               # CSS class names to be used by head tag
                               cssClassNames = '{headerRow: "myTableHeadRow", tableRow: "myTableRow", oddTableRow: "myOddTableRow"}'))
  })
  
})