# Independent frozen R oracle: exact anniversaries, month ends, clocks and fixed random pairs.
source('tests/fixtures/timeinterval-calendar-reference.R')
suppressPackageStartupMessages(library(lubridate))
starts <- c('2024-01-31 15:30:00','2024-01-31 15:30:00','2024-01-31 15:30:00',
            '2023-01-31 00:00:00','2024-02-29 12:00:00','2024-03-31 15:00:00',
            '2024-02-29 15:00:00','2024-03-31 15:00:00')
ends <- c('2024-02-28 15:30:00','2024-02-29 15:30:00','2024-03-01 15:30:00',
          '2023-03-01 00:00:00','2025-02-28 12:00:00','2024-02-29 14:00:00',
          '2024-01-31 15:00:00','2024-03-01 14:00:00')
withr::with_seed(4701, {
  a <- as.POSIXct('1980-01-01',tz='UTC')+sample.int(50*365*86400,400,replace=TRUE)
  b <- a+sample((-1500:1500)*86400,400,replace=TRUE)+sample(-1000:1000,400,replace=TRUE)
  starts <<- c(starts,format(a,'%Y-%m-%d %H:%M:%S',tz='UTC'))
  ends <<- c(ends,format(b,'%Y-%m-%d %H:%M:%S',tz='UTC'))
})
a <- as.POSIXct(starts,tz='UTC');b <- as.POSIXct(ends,tz='UTC')
fixture <- list(reference_commit='381df71e98e4fb460d44e5a6cc439a04289acfdd',
                lubridate=as.character(packageVersion('lubridate')),
                cases=data.frame(start=starts,end=ends,
                    months=calendar_reference(a,b,'months'),years=calendar_reference(a,b,'years')))
jsonlite::write_json(fixture,'tests/fixtures/timeinterval-calendar.json',auto_unbox=TRUE,
                    digits=16,pretty=TRUE)
