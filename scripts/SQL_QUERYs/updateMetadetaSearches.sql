ALTER TABLE metadata_searches
ADD COLUMN id_variables TEXT[] DEFAULT '{}';

ALTER TABLE metadata_searches
ADD COLUMN selected_id_coes TEXT[] DEFAULT '{}';