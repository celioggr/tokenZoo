from statemachine import StateMachine
import brownie,pytest
from brownie import project

@pytest.fixture()
def contract2test():
    token = project.load('/home/honeybadger/2test').AmberToken
    yield token

class AmberToken(StateMachine):
    def __init__(self,accounts,contract2test):
        super().__init__(self,accounts,contract2test)
        self.totalSupply = 0
        self.contract = contract2test.deploy({"from": accounts[0]})

    """Override mint rule since method isMinter() from base StateMachine does not exist in this contract """
    def rule_mint(self,st_receiver,st_minter,st_amount):
        if self.contract.owner():
            self.contract.mint(st_receiver,st_amount,{"from":st_minter})
            self.totalSupply += st_amount
            self.balances[st_receiver] += st_amount
        else:
            with brownie.reverts("MinterRole: caller does not have the Minter role"):
                self.contract.mint(st_receiver,st_amount,{"from":st_minter})

    """Override totalSupply_overflows rule since method isMinter() from base StateMachine does not exist in this contract """
    def rule_totalSupply_overflows(self,st_minter,st_receiver):
        uint256max = 2**256 - 1
        if self.contract.owner():
            tx = self.contract.mint(st_receiver,uint256max,{"from":st_minter})
            self.totalSupply += uint256max
            self.balances[st_receiver] += uint256max
        else:
            with brownie.reverts("MinterRole: caller does not have the Minter role"):
                self.contract.mint(st_receiver,uint256max,{"from":st_minter})

    def rule_decrease_the_allowance(self, st_spender, st_owner,st_amount):
        pass

    def rule_increase_the_allowance(self, st_spender, st_owner,st_amount):
        pass

def test_stateful(contract2test,accounts,state_machine):
    settings = {"stateful_step_count": 10, "max_examples": 40, "print_blob":True}
    state_machine(AmberToken, accounts,contract2test,settings=settings)
