function setupSocketIO() {
	var socket = io.connect('http://' + document.domain + ':' + location.port);
	socket.on('status', function(msg) {
		$('#now_playing_wrapper').html(msg['plex']);
	});
	socket.emit('connect');
}
