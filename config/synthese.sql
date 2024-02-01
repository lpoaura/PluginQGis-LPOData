CREATE INDEX ON gn_synthese.synthese USING btree (st_geometrytype(the_geom_local));
