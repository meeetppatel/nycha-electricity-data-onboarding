let
  dup_keys = Excel.CurrentWorkbook(){[Name="tbl_raw"]}[Content],
  #"Changed column type" = Table.TransformColumnTypes(dup_keys, {{"service_start_date", type date}, {"service_end_date", type date}, {"meter_scope", type text}, {"meter_number", type text}}),
  #"Grouped rows" = Table.Group(#"Changed column type", {"meter_number", "service_start_date", "service_end_date"}, {{"n", each Table.RowCount(_), Int64.Type}})
in
  #"Grouped rows"
