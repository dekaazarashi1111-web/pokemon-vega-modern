/* 完全save fixtureは起動前のみ。観測barrier後に値・座標・文言を書かない。 */
int main(int argc,char**argv){
 if(argc==3&&!strcmp(argv[1],"--guard-check"))si_guard_check(argv[2]);
 si_need(argc==4,"counter numeric fixture args");
 unsigned fixture=qol_number(argv[3],"fixture");si_need(fixture<2,"closed numeric fixture");
 static const char*sha[2]={
  "434076d0db74c4c5bf1b63e3aa4cc336d17e1f2dbb894160e840c721aa337a38",
  "95646d927206354df5f2ad4b0bfca85bc26bd3d1a90811df9988e3ccb0357046"};
 nb_fixture=sha[fixture];nb_balance=fixture?9999:0;nb_lifetime=fixture?2200:0;nb_rank=fixture?7:1;
 char*args[4]={argv[0],argv[1],argv[2],"0"};
 return accepted_connection_main(4,args);
}
