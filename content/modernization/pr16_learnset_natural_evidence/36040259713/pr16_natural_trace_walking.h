/* Issue19: saved physical-learning witness -> explicit initial party fixture ->
 * natural walking encounter -> learned move -> ordinary Save/fresh Continue.
 * No target, RNG, HP/PP, battle function or outcome injection while observed. */
/* GBA keypad left, matching the existing field drivers. */
#define QOL_KEY_LEFT 0x0020U
static unsigned lb_steps,lb_frames,lb_spent,lb_damage,lb_chosen,lb_outcome;
static unsigned lb_before_pp,lb_after_pp,lb_enemy_hp,lb_min_hp;
static bool lb_observe;

static unsigned nt_steps,nt_calls;
static bool lb_action(struct mCore *c);
static void nt_frame(struct mCore *c) {
    unsigned sb=read32(c,QOL_SAVE_BLOCK1_SLOT);
    if(!p02s_ewram_pointer(sb) || read8(c,sb+4)!=96 || read8(c,sb+5)!=17 || lb_action(c)){c->runFrame(c);return;}
    unsigned frame=c->frameCounter(c),steps=0;
    while(c->frameCounter(c)==frame) {
        unsigned pc=(unsigned)read_register(c,"pc");
        unsigned entries[]={0x0803D1C0,0x0803E14C,0x091145F0,read32(c,0x0803E150)&~1U,0x0803E01C,0x0803FBC4,ROM_SET_MON_DATA&~1U};
        for(unsigned i=0;i<sizeof(entries)/sizeof(*entries);++i)if(pc==entries[i]+4 || pc==entries[i]+2) {
            unsigned r0=(unsigned)read_register(c,"r0"),r1=(unsigned)read_register(c,"r1"),r2=(unsigned)read_register(c,"r2"),lr=(unsigned)read_register(c,"lr");
            if(i<5 || (r0>=ADDR_ENEMY_PARTY && r0<ADDR_ENEMY_PARTY+600 && r1>=11 && r1<=25)) {
                unsigned value=p02s_ewram_pointer(r2)?read32(c,r2):0;
                fprintf(stderr,"NATURAL_TRACE frame=%u pc=%08x entry=%08x lr=%08x r0=%08x r1=%08x r2=%08x value=%08x\n",lb_frames,pc,entries[i],lr,r0,r1,r2,value);++nt_calls;
            }
        }
        c->step(c);a_require(++steps<=2000000 && ++nt_steps<=120000000,"bounded passive initial trace");
    }
}

static void lb_frame(struct mCore *c,unsigned key) {
    c->setKeys(c,key);nt_frame(c);++lb_frames;
    if(read8(c,BATTLE_CORE_BATTLE_OUTCOME))lb_outcome=read8(c,BATTLE_CORE_BATTLE_OUTCOME);
    if(lb_observe && read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER)) {
        unsigned pp=read8(c,ADDR_BATTLE_MONS+BATTLE_MON_PP_OFFSET+1U);
        unsigned hp=read16(c,ADDR_BATTLE_MONS+BATTLE_MON_SIZE+BATTLE_CORE_MON_HP);
        unsigned current=read16(c,0x02023CAAU),chosen=read16(c,BATTLE_CORE_CHOSEN_MOVES);
        if(chosen==420U && !lb_chosen)lb_chosen=lb_frames;
        if(pp<lb_before_pp && !lb_spent){lb_spent=lb_frames;lb_after_pp=pp;}
        if(current==420U && hp<lb_min_hp){lb_min_hp=hp;if(!lb_damage)lb_damage=lb_frames;}
    }
}
static void lb_wait(struct mCore *c,unsigned n){for(unsigned i=0;i<n;++i)lb_frame(c,0);}
static void lb_press(struct mCore *c,unsigned key,unsigned n){lb_frame(c,key);lb_wait(c,n);}
static unsigned lb_save1(struct mCore *c){unsigned p=read32(c,QOL_SAVE_BLOCK1_SLOT);a_require(p02s_ewram_pointer(p),"battle save block");return p;}
static bool lb_field(struct mCore *c) {
    unsigned id=read8(c,P02S_PLAYER_AVATAR+5);
    return read32(c,BATTLE_CORE_MAIN_CALLBACK2)==P02S_CB2_FIELD && read8(c,P02S_FIELD_LOCK)==0
        && !read8(c,P02S_QUEST_LOG_STATE) && !read8(c,P02S_QUEST_LOG_PLAYBACK_STATE) && id<16
        && (read8(c,P02S_OBJECT_EVENTS+id*0x24)&1U)
        && !read8(c,P02S_PLAYER_AVATAR+P02S_PLAYER_RUNNING_STATE_OFFSET)
        && !read8(c,P02S_PLAYER_AVATAR+P02S_PLAYER_TILE_TRANSITION_STATE_OFFSET);
}
static bool lb_action(struct mCore *c) {
    unsigned ctrl=read32(c,0x03005020U);
    return read32(c,0x03004FC4U)==0x08013861U && (read32(c,0x02023B28U)&1U)
        && read8(c,0x02022B24U)==0x12U && (ctrl==0x0802DC15U || ctrl==0x09118B85U);
}
static void lb_wait_action(struct mCore *c) {
    for(unsigned i=0;i<12000U;++i){if(lb_action(c)){c->setKeys(c,0);return;}lb_frame(c,i%60U==0?QOL_KEY_A:0);}
    a_die("natural learned-move action controller timeout");
}
static void lb_position(struct mCore *c,unsigned group,unsigned map,unsigned x,unsigned y) {
    unsigned s=lb_save1(c);
    a_require(read8(c,s+4)==group && read8(c,s+5)==map && read16(c,s)==x && read16(c,s+2)==y,"learned-move physical position differs");
}
static void lb_step(struct mCore *c,unsigned key) {
    a_require(lb_field(c),"walking outside field");unsigned s=lb_save1(c),x=read16(c,s),y=read16(c,s+2);bool moved=false;
    for(unsigned i=0;i<90;++i){lb_frame(c,key);s=lb_save1(c);if(read16(c,s)!=x || read16(c,s+2)!=y){moved=true;break;}}
    c->setKeys(c,0);a_require(moved,"learned-move walk blocked");++lb_steps;unsigned stable=0;
    for(unsigned i=0;i<12000;++i){
        if(read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER)){lb_wait_action(c);return;}
        if(lb_field(c)){if(++stable==12)return;}else stable=0;
        lb_frame(c,0);
    }
    a_die("learned-move walking timeout");
}
static void lb_path(struct mCore *c,unsigned map,const unsigned path[][2],unsigned count,bool grass) {
    for(unsigned i=0;i<count;++i){
        unsigned s=lb_save1(c),x=read16(c,s),y=read16(c,s+2),tx=path[i][0],ty=path[i][1];
        lb_position(c,96,map,x,y);
        a_require((x==tx && (y+1==ty || ty+1==y)) || (y==ty && (x+1==tx || tx+1==x)),"nonadjacent path");
        lb_step(c,x<tx?QOL_KEY_RIGHT:x>tx?QOL_KEY_LEFT:y<ty?QOL_KEY_DOWN:QOL_KEY_UP);
        if(read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER)){a_require(grass,"unexpected town encounter");return;}
        lb_position(c,96,map,tx,ty);
    }
}
static void lb_cursor(struct mCore *c,unsigned address,unsigned target) {
    for(unsigned i=0;i<6;++i){unsigned at=read8(c,address);a_require(at<4,"battle cursor invalid");if(at==target)return;
        lb_press(c,(at&1)!=(target&1)?((target&1)?QOL_KEY_RIGHT:QOL_KEY_LEFT):((target&2)?QOL_KEY_DOWN:QOL_KEY_UP),12);}
    a_die("battle cursor did not follow physical input");
}
static void lb_return(struct mCore *c) {
    unsigned stable=0;
    for(unsigned i=0;i<24000;++i){
        unsigned outcome=read8(c,BATTLE_CORE_BATTLE_OUTCOME);if(outcome)lb_outcome=outcome;
        if(!read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER) && lb_field(c)){if(++stable==30){c->setKeys(c,0);return;}}else stable=0;
        if(lb_action(c)){lb_cursor(c,BATTLE_CORE_ACTION_SELECTION_CURSOR,3);lb_press(c,QOL_KEY_A,60);continue;}
        lb_frame(c,i%60==0?QOL_KEY_B:0);
    }
    a_die("learned-move battle did not return");
}
static unsigned lb_resume_x,lb_resume_y;
static bool lb_resume_position(struct mCore *c) {
    unsigned s=lb_save1(c);
    return read8(c,s+4)==96 && read8(c,s+5)==17 && read16(c,s)==lb_resume_x && read16(c,s+2)==lb_resume_y;
}
static bool lb_normal_continue(struct mCore*c) {
    run_key_frames(c,0,P02S_TITLE_FRAMES);
    for(unsigned p=0;p<P02S_CONTINUE_PULSES;p++) {
        qol_press(c,p==0?QOL_KEY_START:QOL_KEY_A,P02S_CONTINUE_WAIT_FRAMES);
        if(read32(c,BATTLE_CORE_MAIN_CALLBACK2)!=P02S_CB2_FIELD || !lb_resume_position(c))continue;
        run_key_frames(c,0,300);
        for(unsigned r=0;r<8;r++) {
            if(!read8(c,P02S_QUEST_LOG_STATE) && !read8(c,P02S_QUEST_LOG_PLAYBACK_STATE)) {
                run_key_frames(c,0,P02S_FIELD_SETTLE_FRAMES);unsigned stable=0;
                for(unsigned f=0;f<3600;f++) {
                    if(lb_field(c)){if(++stable>=P02S_INPUT_READY_FRAMES)return true;}else stable=0;
                    run_key_frames(c,0,1);
                }
            }
            qol_press(c,QOL_KEY_B,P02S_CONTINUE_WAIT_FRAMES);
        }
        return false;
    }
    return false;
}
static bool lb_normal_save(struct mCore*c) {
    unsigned counter=read32(c,P03_SAVE_COUNTER);qol_press(c,QOL_KEY_START,120);
    if(read32(c,QOL_START_MENU_CALLBACK)!=QOL_START_MENU_INPUT)return false;
    unsigned count=read8(c,QOL_START_MENU_COUNT),cursor=read8(c,QOL_START_MENU_CURSOR),target=count;
    if(!count || count>9 || cursor>=count)return false;
    for(unsigned i=0;i<count;i++)if(read8(c,QOL_START_MENU_ORDER+i)==P03_SAVE_ACTION)target=i;
    if(target==count)return false;
    for(unsigned i=0,n=(target+count-cursor)%count;i<n;i++)qol_press(c,QOL_KEY_DOWN,30);
    if(read8(c,QOL_START_MENU_CURSOR)!=target)return false;
    qol_press(c,QOL_KEY_A,120);bool seen=false;
    for(unsigned i=0;i<32;i++) {
        unsigned cb=read32(c,QOL_START_MENU_CALLBACK);if(cb==P03_SAVE_CALLBACK)seen=true;
        if(seen && cb==P03_SAVE_CALLBACK && read32(c,P03_SAVE_COUNTER)==counter+1 && lb_field(c)) {
            run_key_frames(c,0,180);return lb_field(c);
        }
        qol_press(c,QOL_KEY_A,180);
    }
    return false;
}
