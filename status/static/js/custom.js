function setupSocketIO() {
	var socket = io.connect('http://' + document.domain + ':' + location.port);

	socket.on('plex', function(msg) {
		$('#now_playing_wrapper').html(msg['data']);
	});

	socket.on('forecast', function(msg) {
		$('#left_column_top').html(msg['data']);
	});

	socket.on('bandwidth', function(msg) {
		$('#bandwidth').html(msg['data']);
	});

	socket.on('services', function(msg) {
		$('#services').html(msg['data']);
	});

	socket.emit('connect');
}
