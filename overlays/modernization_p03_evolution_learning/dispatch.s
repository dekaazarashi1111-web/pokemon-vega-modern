.syntax unified
.cpu arm7tdmi
.thumb
.section .text
.balign 4
.global Pr16_EvolutionLearningDispatch
.type Pr16_EvolutionLearningDispatch,%function
.thumb_func
Pr16_EvolutionLearningDispatch:
  mov r2, lr
  ldr r3, .Lcaller1
  cmp r2, r3
  beq .Levolution
  ldr r3, .Lcaller2
  cmp r2, r3
  beq .Levolution
  ldr r3, .Lnormal
  bx r3
.Levolution:
  ldr r3, .Lafter
  bx r3
.balign 4
.Lcaller1: .word 0x080CFEF9
.Lcaller2: .word 0x080D0A6D
.Lnormal: .word 0x09377729
.Lafter: .word 0x09114121
