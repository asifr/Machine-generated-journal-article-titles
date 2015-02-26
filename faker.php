<?php
$data = json_decode(file_get_contents('titlesdb.json'),true);
$ids = array(array_rand($data['real'],1), array_rand($data['fake'],1));
$idx = array_rand($ids);
$id = $ids[$idx];
$real = ($idx == 0)?"real":"fake";

exit(json_encode(array(
	'id'=>$id,
	'title'=>trim(ucfirst($data[$real][$id]),'.'),
	'real'=>$real
	)));
?>