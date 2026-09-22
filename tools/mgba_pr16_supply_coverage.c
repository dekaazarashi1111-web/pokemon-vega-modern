/* Keep the accepted runner bytes; expose non-vacuity counters even on failure. */
#define main pr16_original_supply_main
#include "mgba_pr16_learnset_supply.c"
#undef main
static void coverage_summary(void)
{
    fprintf(stderr,"coverage calls=%u readonly=%u tutor_yes=%u tutor_no=%u special_yes=%u special_no=%u page_four=%u filtered=%u log_problem_count=%u\n",
            calls,checks,tutor_yes,tutor_no,specials_yes,specials_no,page_four,filtered,(unsigned)log_problem_count);
}
int main(int argc,char **argv)
{
    if(atexit(coverage_summary))return 2;
    return pr16_original_supply_main(argc,argv);
}
