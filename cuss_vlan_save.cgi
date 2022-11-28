#!/usr/bin/perl
# cuss_valn_save.cgi
# Custom script - save and apply VLAN's changes

require './net-lib.pl';
%net_text = &load_language('net');
#$, = '<br>';
sub check_route {
	my ($dest,$gate,$src_ip,$src_mask) = @_;
	my ($dest_ip,$dest_mask) = ($dest =~ /((?:\d{1,3}\.){3}\d{1,3})\/(\d{1,2})/)?($1,&prefix_to_mask($2)):("","");
	&check_ipaddress_any($dest_ip) || &error($net_text{'routes_ecdest'});
	&check_netmask($dest_mask,$dest_ip) || &error($net_text{'routes_ecnetmask'});
	&check_ipaddress_any($gate) || &error($net_text{'routes_ecgw'});
	&error("Шлюз $gate/".&mask_to_prefix($src_mask)." и интерфейс $src_ip находятся в разных подсетях.") if &compute_network($gate, $src_mask) ne &compute_network($src_ip, $src_mask);
    #return 1;
	}
sub clear_route {
	$yaml->[$rows{'routes'}] =~ s/^\s+\S+$/#$&/;
	for (my $i=0; $i < @{$rows{'dst'}}; $i++){
		$yaml->[$rows{'dst'}[$i]] =~ s/^\s+-\s*to:\s*\S+$/#$&/ if !$i;
		$yaml->[$rows{'gate'}[$i]] =~ s/^\s+via:\s*\S+$/#$&/ if !$i;
		$yaml->[$rows{'dst'}[$i]] = 0 if $i;
		$yaml->[$rows{'gate'}[$i]] = 0 if $i;
		}
	}

&ReadParse();

@act = &active_interfaces(1);
$a = $act[$in{'idx'}];
&error_setup($net_text{'aifc_err2'});

$vlan = $a->{'fullname'} =~ /vlan(\d+)/ ? $1 : '';
$file_path = (glob("$netplan_dir/*.${vlan}*.yaml"))[0];
&copy_source_dest($file_path,$file_path.'.back');
$yaml = &read_file_lines($file_path);
$has_route = $in{'routes'} eq 'on' ? 1 : 0;
@out = ();

#Find rows for edit
%rows = (
		'addresses',0,
		'ip',0,		
		'comment',0,
		'routes',0,
		'dst', (),
		'gate', ()
		);
for (my $i=0; $i < @$yaml; $i++){
	$rows{'comment'} = $i if $yaml->[$i] =~ /^###.*$/;
	$rows{'addresses'} = $i if $yaml->[$i] =~ /^#?\s+addresses:$/;
	$rows{'ip'} = $i if $yaml->[$i] =~ /^#?\s+-\s+(?:\d{1,3}\.){3}\d{1,3}\/\d{1,2}$/;
	$rows{'routes'} = $i if $yaml->[$i] =~ /^#?\s+routes:$/;
	push(@{$rows{'dst'}}, $i) if $yaml->[$i] =~ /^#?\s+-\s+to:\s+(?:\d{1,3}\.){3}\d{1,3}\/\d{1,2}$/;
	push(@{$rows{'gate'}}, $i) if $yaml->[$i] =~ /^#?\s+via:\s+(?:\d{1,3}\.){3}\d{1,3}$/;
	}

#print "Content-type: text/html; charset=utf-8\n\n";

# Validate and save inputs
if ($in{'address'} !~ /\S/) {
	# Clear VLAN intarface
	$yaml->[$rows{'addresses'}] =~ s/^\s+\S+$/#$&/;
	$yaml->[$rows{'ip'}] =~ s/^\s+-\s*\S+$/#$&/;
	$yaml->[$rows{'comment'}] = "###";
	clear_route();
	}
elsif (&check_ipaddress_any($in{'address'})) {
    # Save new values
	$in{'comment'} = &un_urlize($in{'comment'});
	&check_netmask($in{'netmask'},$in{'address'}) || &error(&text('aifc_emask', &html_escape($in{'netmask'})));
	$in{'address'} .= '/'.&mask_to_prefix($in{'netmask'});
	&error('Не заполнен Комментарий') if $in{'comment'} !~ /\S/;
	#$yaml->[$rows{'comment'}] = $rows{'comment'} ? "###".$in{'comment'} : $yaml->[$rows{'comment'}] ."\n"."###".$in{'comment'};
	$yaml->[$rows{'comment'}] = "###".$in{'comment'};
	$yaml->[$rows{'addresses'}] =~ s/^#?(\s+addresses:)$/$1/;
	$yaml->[$rows{'ip'}] =~ /^#?(\s+-\s+)(?:\d{1,3}\.){3}\d{1,3}\/\d{1,2}$/;
	$yaml->[$rows{'ip'}] = $1.$in{'address'};
	if ($has_route) {
		my ($r,$d,$g) = (scalar @{$rows{'dst'}}, "", "");
		check_route($in{'dst_0'},$in{'gate_0'},$in{'address'},$in{'netmask'});
		$yaml->[$rows{'routes'}] =~ s/^#?(\s+routes:)$/$1/;	
		for($i=0; defined($in{'dst_'.$i}); $i++) {
			next if ($in{'dst_'.$i} !~ /\S/);
			check_route($in{'dst_'.$i},$in{'gate_'.$i},$in{'address'},$in{'netmask'});
			$in{'dst_'.$i} = &un_urlize($in{'dst_'.$i});
			if ($i < $r ) {
                $yaml->[$rows{'dst'}->[$i]] =~ /^#?(\s+-\s+to:\s+)(?:\d{1,3}\.){3}\d{1,3}\/\d{1,2}$/;
				$d = $1;
				$yaml->[$rows{'dst'}->[$i]] = $d.$in{'dst_'.$i};
				$yaml->[$rows{'gate'}->[$i]] =~ /^#?(\s+via:\s+)(?:\d{1,3}\.){3}\d{1,3}$/;
				$g = $1;
				$yaml->[$rows{'gate'}->[$i]] = $g.$in{'gate_'.$i};
				}
			else {
				$yaml->[$rows{'gate'}->[$r-1]] .= "\n".$d.$in{'dst_'.$i}."\n".$g.$in{'gate_'.$i};
				}
			}	
		}
	else{ clear_route(); }
	}
else {
	&error(&text('aifc_eip', &html_escape($in{'address'})));
	}

for (my $i=0; $i < @$yaml; $i++){
	next if !$yaml->[$i];
	push (@out,$yaml->[$i]);
}
@$yaml = @out;
&flush_file_lines($file_path);

# Bring it up
$cmd = "netplan apply 2>&1";
$err = &backquote_logged($cmd);
if ($?) {
	&copy_source_dest($file_path.'.back',$file_path);
    &error("Невозможно активировать интерфейс: $err");
}

&webmin_log('modify', "aifc", $a->{'fullname'}, $a);
&redirect("cuss_vlan_list.cgi?ok=$vlan");

