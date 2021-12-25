library(tidyverse)

library(reticulate)
library(jsonlite)
library(httr)


req <- POST("https://ke-ap01.econ.muni.cz/getData.php", 
          body = list(
            name = "*",
            time = "2021-12-25 11:00:00"
          ),
          encode = "json")

req$status_code
content(req, as = "text")

stop_for_status(req)
json <- content(req, "text")
json
