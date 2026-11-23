let
  Raw_flagged = Excel.CurrentWorkbook(){[Name="tbl_raw"]}[Content],
  #"Changed column type" = Table.TransformColumnTypes(Raw_flagged, {{"service_end_date", type date}, {"service_start_date", type date}, {"consumption_kwh", type number}, {"consumption_kw", type number}, {"kwh_charges", type number}, {"estimated", type text}, {"meter_number", type text}}),
  #"Added custom" = Table.AddColumn(#"Changed column type", "pq_demand_only", each ([consumption_kwh] ?? 0) = 0 and ([consumption_kw] ?? 0) > 0),
  #"Added custom 1" = Table.AddColumn(#"Added custom", "pq_kwh_missing", each ([consumption_kwh] ?? 0) = 0 and ([kwh_charges] ?? 0) > 0),
  #"Added custom 2" = Table.AddColumn(#"Added custom 1", "pq_est", each [estimated] = "Y"),
  #"Changed column type 1" = Table.TransformColumnTypes(#"Added custom 2", {{"pq_demand_only", type logical}, {"pq_kwh_missing", type logical}, {"pq_est", type logical}}),
  #"Merged queries" = Table.NestedJoin(#"Changed column type 1", {"meter_number", "service_start_date", "service_end_date"}, dup_keys, {"meter_number", "service_start_date", "service_end_date"}, "dup_keys", JoinKind.LeftOuter),
  #"Expanded dup_keys" = Table.ExpandTableColumn(#"Merged queries", "dup_keys", {"n"}, {"n"}),
  #"Added custom 3" = Table.TransformColumnTypes(Table.AddColumn(#"Expanded dup_keys", "pq_dup", each [n] > 1), {{"pq_dup", type logical}}),
  #"Added custom 4" = Table.TransformColumnTypes(Table.AddColumn(#"Added custom 3", "flags_match", each [pq_demand_only] = [flag_demand_only] and [pq_kwh_missing] = [flag_kwh_missing] and [pq_est] = [flag_est] and [pq_dup] = [flag_dup]), {{"flags_match", type logical}}),
  #"Choose columns" = Table.SelectColumns(#"Added custom 4", {"source_row_id", "pq_demand_only", "pq_kwh_missing", "pq_est", "pq_dup", "flags_match"})
in
  #"Choose columns"
