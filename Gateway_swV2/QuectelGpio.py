import onionGpio

lte_ri = onionGpio.OnionGpio(17)
lte_reset = onionGpio.OnionGpio(16)
lte_n_wake = onionGpio.OnionGpio(15)
lte_wakeup = onionGpio.OnionGpio(14)


lte_reset.setOutputDirection()
lte_wakeup.setOutputDirection()
lte_n_wake.setInputDirection()
lte_ri.setInputDirection()

lte_reset.setValue(1)
lte_wakeup.setValue(1)