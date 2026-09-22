/* Preserve nested main macros in the existing runner; only add exit diagnostics. */
#include "mgba_pr16_learnset_supply.c"
static void coverage_summary(void)
{
    fprintf(stderr,"coverage calls=%u readonly=%u tutor_yes=%u tutor_no=%u special_yes=%u special_no=%u page_four=%u filtered=%u log_problem_count=%u\n",
            calls,checks,tutor_yes,tutor_no,specials_yes,specials_no,page_four,filtered,(unsigned)log_problem_count);
}
/* Host GCC/Clang only. This does not replace main or alter the acceptance oracle. */
__attribute__((constructor)) static void register_coverage_summary(void)
{
    if(atexit(coverage_summary))abort();
}
