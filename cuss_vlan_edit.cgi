#!/usr/bin/perl
# cuss_valn_edit.cgi
# Custom script - display VLAN's edit form

require './net-lib.pl';
&ReadParse();
@act = &active_interfaces(1);
%net_text = &load_language('net');

$a = $act[$in{'idx'}];

#Gettin Routes and Comment from *.yaml
$a->{'comment'} = "";
$a->{'dst'} = ();
$a->{'gate'} = ();

$vlan = $a->{'fullname'} =~ /vlan(\d+)/ ? $1 : '';
$yaml = &read_file_lines((glob("$netplan_dir/*.${vlan}*.yaml"))[0]);
$has_route = 0;
foreach my $l (@$yaml){
	$a->{'comment'} = $1 if $l =~ /^###\s*(.+)\s*$/; 
	$has_route = 1 if $l =~ /^\s+routes:/;
	push(@{$a->{'dst'}}, $1) if ($l =~ /^\s+-\s*to:\s*((?:\d{1,3}\.){3}\d{1,3}\/\d{1,2})$/ && $has_route);
	push(@{$a->{'gate'}}, $1) if ($l =~ /^\s+via:\s*((?:\d{1,3}\.){3}\d{1,3})$/ && $has_route);
}
    

#&can_iface($a) || &error($text{'ifcs_ecannot_this'});
#&ui_print_header(undef, $text{'aifc_edit'}, "");

# Editing existing interface

&ui_print_header(undef,$a->{'fullname'}, "",undef,undef,1);

# Form start
print &ui_form_start("cuss_vlan_save.cgi"); # скрипт формы
print &ui_hidden("idx", $in{'idx'});
print &ui_table_start('Настройка интерфейса', undef, 2);

# IP address
print &ui_table_row($net_text{'ifcs_ip'}, &ui_textbox("address", $a->{'address'} , 15));

# Netmask field
print &ui_table_row($net_text{'ifcs_mask'}, &ui_textbox("netmask", $a->{'netmask'}, 15));

# Comment
print &ui_table_row('№ ЛРП/Комментарий', &ui_textbox("comment", $a->{'comment'}, 30));


# Show the Routes field
$routestable = &ui_columns_start([ "Сеть назначения","Шлюз" ], 50);
for($i=0; $i<=@{$a->{'dst'}}; $i++) {
		$routestable .= &ui_columns_row([
		    &ui_textbox("dst_$i",
				$a->{'dst'}->[$i], 15),
		    &ui_textbox("gate_$i",
				$a->{'gate'}->[$i], 15) ]);
	}
$routestable .= &ui_columns_end();
print &ui_table_row('Маршруты',
	&ui_radio_table("routes",
		$has_route ? "on" : "off",
			[ [ "off", 'Выключить'],
			  [ "on", 'Включить', $routestable ] ]), 2);




# End of the form
print &ui_table_end();

@buts = ( [ undef, $net_text{'save'} ] );
print &ui_form_end(\@buts);

&ui_print_footer("cuss_vlan_list.cgi", 'списку VLAN');

