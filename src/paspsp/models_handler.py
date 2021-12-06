'''
Class to identify a world.
In the constructor, both lower and upper int (counters) are needed, since in 
some cases only model_not_query is true, so the world does not contribute
to the list
'''

from typing import List, Union
import utilities
import math

import sys


class World:
    '''
    id is the string composed by the occurrences of the variables
    '''
    def __init__(self, id : str, prob : int) -> None:
        self.id : str = id
        self.prob : int = prob
        # meaning of these two: 
        # if not evidence: model_not_query_count -> q 
        #                  model_query_count -> q
        # if evidence: model_not_query_count -> q and e
        #              model_query_count -> nq and e
        self.model_not_query_count : int = 0
        self.model_query_count : int = 0
        # this is needed only on the case of evidence, to count the models
        self.model_count : int = 0
    
    def get_id(self) -> str:
        return self.id
    
    def get_prob(self) -> int:
        return self.prob

    def get_model_query_count(self) -> int:
        return self.model_query_count
    
    def get_model_not_query_count(self) -> int:
        return self.model_not_query_count
    
    def get_model_count(self) -> int:
        return self.model_count

    def increment_model_not_query_count(self) -> None:
        self.model_not_query_count = self.model_not_query_count + 1

    def increment_model_query_count(self) -> None:
        self.model_query_count = self.model_query_count + 1

    def increment_model_count(self) -> None:
        self.model_count = self.model_count + 1

    def __str__(self) -> str:
        return "id: " + self.id + " prob: " + str(self.prob) + \
            " mqc: " + str(self.get_model_query_count()) + \
            " mnqc: " + str(self.get_model_not_query_count()) + \
            " mc: " + str(self.get_model_count())
    
'''
Class to handle the models computed by clingo.
'''
class ModelsHandler():
    def __init__(self, precision : int, n_prob_facts : int, evidence : str) -> None:
        self.worlds_dict = dict()
        self.upper_query_prob : float = 0
        self.lower_query_prob : float = 0
        self.upper_evidence_prob : float = 0
        self.lower_evidence_prob : float = 0
        self.precision : int = precision
        self.n_prob_facts : int = n_prob_facts
        self.evidence : str = evidence

    def increment_lower_query_prob(self, p : float) -> None:
        self.lower_query_prob = self.lower_query_prob + p

    def increment_upper_query_prob(self, p : float) -> None:
        self.upper_query_prob = self.upper_query_prob + p

    def increment_lower_evidence_prob(self, p : float) -> None:
        self.lower_evidence_prob = self.lower_evidence_prob + p

    def increment_upper_evidence_prob(self, p: float) -> None:
        self.upper_evidence_prob = self.upper_evidence_prob + p

    def get_number_worlds(self) -> int:
        return len(self.worlds_dict.keys())

    # checks if the id is in the worlds list
    # query = True -> q in line
    # query = False -> nq in line
    # model_evidence = True -> e in line
    # model_evidence = False -> ne in line
    def manage_worlds_dict(self, id : str, prob : int, model_query : bool, model_evidence : bool) -> None:
        if id in self.worlds_dict:
            if self.evidence is None:
                if model_query == True:
                    self.worlds_dict[id].increment_model_query_count()
                else:
                    self.worlds_dict[id].increment_model_not_query_count()
            else:
                self.worlds_dict[id].increment_model_count()
                if (model_query == True) and (model_evidence == True):
                    self.worlds_dict[id].increment_model_query_count()  # q e
                elif (model_query == False) and (model_evidence == True):
                    self.worlds_dict[id].increment_model_not_query_count() # nq e
            return
        
        # element not found -> add a new world
        w = World(id,prob)
        if self.evidence is None:
            if model_query == True:
                w.increment_model_query_count()
            else:
                w.increment_model_not_query_count()
        else:
            w.increment_model_count()
            if (model_query == True) and (model_evidence == True):
                w.increment_model_query_count()  # q e
            elif (model_query == False) and (model_evidence == True):
                w.increment_model_not_query_count()  # nq e
        
        self.worlds_dict[id] = w

    # gets the stable model, extract the probabilities etc
    def add_value(self, line : str) -> None:
        # print(line)
        id, prob, model_query, model_evidence = utilities.get_id_prob_world(line,self.evidence)
        self.manage_worlds_dict(id, prob, model_query, model_evidence)
    
    # computes the lower and upper probability
    def compute_lower_upper_probability(self) -> Union[int,int,int,int]:
        for w in self.worlds_dict:
            p = (self.worlds_dict[w].get_prob() /
                 ((10**self.precision) ** self.n_prob_facts))
            if self.evidence is None:
                if self.worlds_dict[w].get_model_query_count() != 0:
                    if self.worlds_dict[w].get_model_not_query_count() == 0:
                        self.increment_lower_query_prob(p)
                    self.increment_upper_query_prob(p)
            else:
                mqe = self.worlds_dict[w].get_model_query_count()
                mnqe = self.worlds_dict[w].get_model_not_query_count()
                nm = self.worlds_dict[w].get_model_count()
                if mqe > 0:
                    if mqe == nm:
                        self.increment_lower_query_prob(p)
                    self.increment_upper_query_prob(p)
                if mnqe > 0:
                    if mnqe == nm:
                        self.increment_lower_evidence_prob(p)
                    self.increment_upper_evidence_prob(p) 

        if self.evidence is None:
            return self.lower_query_prob, self.upper_query_prob
        else:
            if (self.upper_query_prob + self.lower_evidence_prob == 0) and self.upper_evidence_prob > 0:
                return 0,0
            elif (self.lower_query_prob + self.upper_evidence_prob == 0) and self.upper_query_prob > 0:
                return 1,1
            else:
                return self.lower_query_prob / (self.lower_query_prob + self.upper_evidence_prob), self.upper_query_prob / (self.upper_query_prob + self.lower_evidence_prob)


    def __repr__(self) -> str:
        s = ""
        for el in self.worlds_dict:
            s = s + str(el) + "\n"
        return s
