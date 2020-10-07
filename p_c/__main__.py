
from p_c.input_process import get_import_goods
from p_c.output_process.output_processor import OutputProcessor

goods = get_import_goods()
OutputProcessor(goods).process()



