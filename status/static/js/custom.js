function setupSocketIO() {
	var socket = io.connect('http://' + document.domain + ':' + location.port);

	socket.on('plex', function(msg) {
		$('#now_playing_wrapper').html(msg['data']);
	});
	socket.emit('connect');
}
