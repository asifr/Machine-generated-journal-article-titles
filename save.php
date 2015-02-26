<?php
file_put_contents('fakerdata.txt', sprintf("%s,%s,%s\n",$_GET['id'],$_GET['actual'],$_GET['choice']),FILE_APPEND);
?>