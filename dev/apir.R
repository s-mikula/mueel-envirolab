library(tidyverse)
library(jsonlite)
library(httr)
library(lubridate)

timeg <- Sys.time() - 165


req <- POST("https://ke-ap01.econ.muni.cz/getData.php", 
          body = list(
            name = '*',
            time = as.character(timeg)
          ),
          encode = "json")

req$status_code
content(req, as = "text")
stop_for_status(req)
