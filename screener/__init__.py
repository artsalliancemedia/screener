__version__ = '0.0.1'

# Globalise the list of error responses so these can be put into a convenient table in the docs when consuming the API.
rsp_codes = {
	0: {'status': 0}, # Success
	1: {'status': 1, 'err_msg': 'CPL not found'},
	2: {'status': 2, 'err_msg': 'Playlist not found'},
	3: {'status': 3, 'err_msg': 'No CPL or Playlist loaded'},
	4: {'status': 4, 'err_msg': 'CPL loaded. Load a playlist to skip'},
	5: {'status': 5, 'err_msg': 'No playlist loaded'},
	6: {'status': 6, 'err_msg': 'Position not found'},
	7: {'status': 7, 'err_msg': 'Playlist event not found'},
	8: {'status': 8, 'err_msg': 'Invalid playlist supplied'},
	9: {'status': 9, 'err_msg': 'Schedule mode not recognised'},
	10: {'status': 10, 'err_msg': 'Schedule not found'},
	11: {'status': 11, 'err_msg': 'Ingest not found'}
}