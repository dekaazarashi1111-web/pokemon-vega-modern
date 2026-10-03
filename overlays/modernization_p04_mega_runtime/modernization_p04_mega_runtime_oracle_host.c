#include "modernization_p04_mega_runtime_oracle.h"

#include <stdio.h>

static unsigned assertions;
static unsigned failures;

#define EXPECT(expression) do { \
    ++assertions; \
    if (!(expression)) { \
        ++failures; \
        fprintf(stderr, "FAIL line=%d expression=%s\n", __LINE__, #expression); \
    } \
} while (0)

int main(void)
{
    int side_used = 0;
    P04MegaUsageState usage = {0, 0};
    const P04MegaEvolutionEntry raichu[] = {
        {P04_MEGA_EVO_METHOD, 1032, 1656, P04_MEGA_VARIANT_STANDARD},
        {P04_MEGA_EVO_METHOD, 1033, 1657, P04_MEGA_VARIANT_STANDARD},
        {P04_MEGA_EVO_NONE, 30, 0, 0},
        {P04_MEGA_EVO_METHOD, 1040, 1664, P04_MEGA_VARIANT_STANDARD}
    };
    const P04MegaEvolutionEntry mega_raichu_x[] = {
        {P04_MEGA_EVO_METHOD, 0, 26, P04_MEGA_VARIANT_STANDARD},
        {P04_MEGA_EVO_NONE, 0, 0, 0}
    };
    const size_t raichu_count = sizeof(raichu) / sizeof(raichu[0]);
    const size_t mega_count = sizeof(mega_raichu_x) / sizeof(mega_raichu_x[0]);

    EXPECT(!P04MegaRuntime_ProjectPolicyAllows(0, 0));
    EXPECT(P04MegaRuntime_ProjectPolicyAllows(1, 0));
    EXPECT(!P04MegaRuntime_ProjectPolicyAllows(1, 1));
    EXPECT(P04MegaRuntime_KeystoneEnabled(P04_MEGA_MODE_NORMAL, 1));
    EXPECT(!P04MegaRuntime_KeystoneEnabled(P04_MEGA_MODE_NORMAL, 0));
    EXPECT(P04MegaRuntime_KeystoneEnabled(P04_MEGA_MODE_FRONTIER, 0));
    EXPECT(P04MegaRuntime_KeystoneEnabled(P04_MEGA_MODE_LINK, 0));
    EXPECT(!P04MegaRuntime_KeystoneEnabled(P04_MEGA_MODE_BRAWL, 0));

    EXPECT(P04MegaRuntime_Resolve(raichu, raichu_count, 1032, 1, 1, 0) == 1656);
    EXPECT(P04MegaRuntime_Resolve(raichu, raichu_count, 1033, 1, 1, 0) == 1657);
    EXPECT(P04MegaRuntime_Resolve(raichu, raichu_count, 1040, 1, 1, 0) == 0);
    EXPECT(P04MegaRuntime_Resolve(raichu, raichu_count, 1032, 0, 1, 0) == 0);
    EXPECT(P04MegaRuntime_Resolve(raichu, raichu_count, 1032, 1, 0, 0) == 0);
    EXPECT(P04MegaRuntime_Resolve(raichu, raichu_count, 1032, 1, 1, 1) == 0);
    EXPECT(P04MegaRuntime_Revert(mega_raichu_x, mega_count) == 26);
    EXPECT(P04MegaRuntime_NormalizeBoundary(1656, mega_raichu_x, mega_count,
           P04_MEGA_BOUNDARY_SWITCH) == 1656);
    EXPECT(P04MegaRuntime_NormalizeBoundary(1656, mega_raichu_x, mega_count,
           P04_MEGA_BOUNDARY_FAINT) == 26);
    EXPECT(P04MegaRuntime_NormalizeBoundary(1656, mega_raichu_x, mega_count,
           P04_MEGA_BOUNDARY_BATTLE_END) == 26);
    EXPECT(P04MegaRuntime_NormalizeBoundary(1656, mega_raichu_x, mega_count,
           P04_MEGA_BOUNDARY_INTERRUPT) == 26);
    EXPECT(P04MegaRuntime_NormalizeBoundary(1656, mega_raichu_x, mega_count,
           P04_MEGA_BOUNDARY_SAVE) == 26);

    EXPECT(!P04MegaRuntime_UpstreamOwnerAlreadyUsed(0, 0, 0));
    usage = P04MegaRuntime_UpstreamMark(P04_MEGA_MODE_NORMAL, usage, 0);
    EXPECT(usage.bank_done);
    EXPECT(usage.partner_done);
    EXPECT(P04MegaRuntime_UpstreamOwnerAlreadyUsed(
        usage.bank_done, usage.partner_done, 0));
    EXPECT(!P04MegaRuntime_UpstreamOwnerAlreadyUsed(0, 1, 1));

    usage.bank_done = 0;
    usage.partner_done = 0;
    usage = P04MegaRuntime_UpstreamMark(P04_MEGA_MODE_NORMAL, usage, 1);
    EXPECT(usage.bank_done);
    EXPECT(!usage.partner_done);

    usage.bank_done = 0;
    usage.partner_done = 0;
    usage = P04MegaRuntime_UpstreamMark(P04_MEGA_MODE_BRAWL, usage, 0);
    EXPECT(!usage.bank_done && !usage.partner_done);
    EXPECT(!P04MegaRuntime_UpstreamOwnerAlreadyUsed(
        usage.bank_done, usage.partner_done, 0));

    EXPECT(P04MegaRuntime_ProjectPolicyAllows(1, side_used));
    EXPECT(P04MegaRuntime_ProjectPolicyMark(1, &side_used));
    EXPECT(side_used);
    EXPECT(!P04MegaRuntime_ProjectPolicyAllows(1, side_used));

    /* faint後はbaseへ戻るがusage doneは継続し、revive後の再Megaを拒否する。 */
    EXPECT(P04MegaRuntime_Resolve(raichu, raichu_count, 1032, 1, 1, 1) == 0);

    printf("{\"status\":\"%s\",\"assertions\":%u,\"failures\":%u}\n",
           failures == 0 ? "PASS" : "FAIL", assertions, failures);
    return failures == 0 ? 0 : 1;
}
