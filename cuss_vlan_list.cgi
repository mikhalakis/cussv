#!/usr/bin/perl
# cuss_vlan_list.cgi
# Custom script - listing VLANs for edit
###########################-FIXED-####################################
## Function active_interfaces in ./linux-lib.pl has an error.
## line 41:
## 		elsif ($l =~ /^\d:\s+([^ \t\r\n\@]+\d+)@([^ \t\r\n\@]+\d+):/) {
## should be:
##		elsif ($l =~ /^\d+:\s+([^ \t\r\n\@]+\d+)@([^ \t\r\n\@]+\d+):/) {
###########################-FIXED-####################################
require './net-lib.pl';
&ReadParse();
#$access{'ifcs'} || &error($text{'ifcs_ecannot'});
# Get interfaces
@act = &active_interfaces(1);
%net_text = &load_language('net');
$ok = $in{'ok'}?$in{'ok'}:'0000';
$ro = $in{'ro'}?' (только чтение)':'';
&ui_print_header(undef, "Список VLAN$ro", "",undef,undef,1);

sub get_comment {
	my ($vlan) = @_;
	$vlan  =~ /vlan(\d+)/;
	$vlan = $1;
	if(my @f = glob("$netplan_dir/*.${vlan}*.yaml")){
		my $yaml = &read_file_lines($f[0]);
		foreach my $l (@$yaml){
			next if $l !~ /^###\s*(.+)\s*$/;
			return $1;
		}
	}
	return '';
}

# Show interfaces are currently active

# Table heading
local @tds;
push(@tds, "width=20% valign=top", "width=20% valign=top","width=20% valign=top","width=40% valign=top");
print &ui_columns_start([$net_text{'ifcs_name'}, $net_text{'ifcs_ip'}, $net_text{'ifcs_mask'},'Комментарий'], 100, 0, \@tds);

# Show table of VLANs
@act = sort iface_sort @act;
foreach $a (@act) {
	next if (!($a->{'name'} =~ /vlan\d+/i)); #Include only interfases which names start as 'vlan##'.
    next if ($a->{'name'} =~ /vlan77/i); #Exclude some VLAN from listing. 
	local @cols;
	if (!$ro) {
        push(@cols,	"&nbsp;&nbsp;<a href=\"cuss_vlan_edit.cgi?idx=$a->{'index'}\">". &html_escape($a->{'fullname'})."</a>".($a->{'name'} =~ /vlan$ok/i ? '&nbsp;&nbsp;-&nbsp;OK!' :''));
    }else{
		push(@cols,	"&nbsp;&nbsp;". &html_escape($a->{'fullname'}));
	}
    
	push(@cols, &html_escape($a->{'address'}) ||
			$net_text{'ifcs_noaddress'});
	push(@cols, &html_escape($a->{'netmask'}) ||
			$net_text{'ifcs_nonetmask'});
	push(@cols, &html_escape(get_comment($a->{'name'})));
	print &ui_columns_row([ @cols ], \@tds);
	}
print &ui_columns_end();
&ui_print_footer("../custom/","списку команд");
