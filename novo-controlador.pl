use Net::SSH::Expect;

($pwd, $type, $host,$controller,$uri,$global_ip, $global_hw, $cid, $crossdomain) = @ARGV;
my $ssh = Net::SSH::Expect->new (
   host => $host, 
   password=> '123', 
   user => 'root', 
   raw_pty => 1,
   timeout=> 3
);

my $login_output = $ssh->login();
if ($login_output !~ /# $/) {
    die "Login has failed. Login output was $login_output";
}


$ssh->send("hm=`hostname`");   # using send() instead of exec()
$ssh->waitfor("/# $/");
$ssh->send("folder=`echo $pwd | sed \"s/n[0-9]/\$hm/\"`");
$ssh->waitfor("/# $/");
$ssh->send("cd \$folder");
$ssh->waitfor("/# $/");
$ssh->send("pwd");
$ssh->waitfor("/# $/");
if (defined $uri){
	$ssh->send("bash /home/openwimesh/migrate_controller.sh $type $controller $uri $global_ip $global_hw $cid $crossdomain");
}else{
	$ssh->send("bash /home/openwimesh/migrate_controller.sh $type $controller");
}
my $line;
# returns the next line, removing it from the input stream:
while ( defined ($line = $ssh->read_line()) ) {
	print $line . "\n";  
}
#$pwd =~ s/n[0-9]/$hostname/g;
#my $out = $ssh->exec("echo $pwd");
#print($out);
#my $folder = $ssh->exec("cd $pwd; pwd");
#print($folder);
#my $cmd = $ssh->exec("bash /home/openwimesh/migrate_controller.sh $controller $uri $global_ip $global_hw $cid $crossdomain");
#print($cmd);


$ssh->close();

