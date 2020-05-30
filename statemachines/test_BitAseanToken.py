from statemachine import StateMachine
import brownie,pytest
from brownie import project

@pytest.fixture()
def contract2test():
    token = project.load('/home/honeybadger/2test').BitAseanToken
    yield token

class BitAseanToken(StateMachine):
    def __init__(self,accounts,contract2test):
        super().__init__(self,accounts,contract2test)
        self.totalSupply = 1000
        self.contract = contract2test.deploy(1000,"BitAseanToken",10,"BAT",{"from": accounts[0]})

    def rule_mint(self,st_receiver,st_minter,st_amount):
        if self.contract.owner():
            self.contract.mintToken(st_receiver,st_amount,{"from":st_minter})
            self.totalSupply += st_amount
            self.balances[st_receiver] += st_amount
        else:
            with brownie.reverts():
                self.contract.mintToken(st_receiver,st_amount,{"from":st_minter})

    def rule_totalSupply_overflows(self,st_minter,st_receiver):
        uint256max = 2**256 - 1
        if self.contract.owner():
            tx = self.contract.mintToken(st_receiver,uint256max,{"from":st_minter})
            self.totalSupply += uint256max
            self.balances[st_receiver] += uint256max
        else:
            with brownie.reverts():
                self.contract.mintToken(st_receiver,uint256max,{"from":st_minter})

    def rule_edge_cases(self):
        ZERO_ADDRESS = brownie.network.account.Account('0x0000000000000000000000000000000000000000')
        with brownie.reverts():
            self.contract.transferFrom(ZERO_ADDRESS,self.accounts[4],0,{'from':self.accounts[0]})
        with brownie.reverts():
            self.contract.transferFrom(self.accounts[4],ZERO_ADDRESS,0,{'from':self.accounts[0]})

    def rule_decrease_the_allowance(self, st_spender, st_owner,st_amount):
        pass

    def rule_increase_the_allowance(self, st_spender, st_owner,st_amount):
        pass

def test_stateful(contract2test,accounts,state_machine):
    settings = {"stateful_step_count": 10, "max_examples": 40, "print_blob":True}
    state_machine(BitAseanToken, accounts,contract2test,settings=settings)
