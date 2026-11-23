let
  Clean_Activity = Excel.CurrentWorkbook(){[Name="tbl_clean"]}[Content],
  #"Changed column type" = Table.TransformColumnTypes(Clean_Activity, {{"period_start", type date}, {"period_end", type date}})
in
  #"Changed column type"
