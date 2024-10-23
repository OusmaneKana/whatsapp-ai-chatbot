from openai import OpenAI
from configparser import ConfigParser



DEFAULT_SYSTEM_ROLE = "You are a very friendly and cordial booking assistant at an Airbnb."\
                    " Customers will talk to you about things like: \n \n- Current Rates "\
                    "(which are $79 per night for 1 guest. That includes breakfast and Transport at the airport)."\
                    " For any additional guest there is an extra $30 charge. \n- Guide guests to the right person when"\
                    " you don't know an answer. Either to Mr. Ousmane Ciss who speaks english, wolof and french his"\
                    "number +1 8329704070. Or to Mrs. Ciss who speaks english, wolof, french and Japanase her number"\
                    "is +81 80-4496-2427. \n\n- The Airbnb is located at about 3 kilometers from the Blaise Diagne international"\
                    " Airport. It is located in Diass, Senegal. The website of the place is www.biranelodge.com\n\n- "" Some extra"\
                    " services we offer are restauration and car rental with chauffeur. "

class Bot:
    def __init__(self, openai_apikey) -> None:
        self.client = OpenAI(api_key=openai_apikey)



    def chat(self, prompt, system_role_content = DEFAULT_SYSTEM_ROLE):
       
        # Call the OpenAI API
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                "role": "system",
                "content": [
                    {
                    "text": system_role_content,
                    "type": "text"
                    }
                ]
                },
                {
                    "role": "user",
                    "content":prompt
                }
            ],
            temperature=1,
            max_tokens=2048,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
            response_format={
                "type": "text"
            },
            
            )
        
        # Parse the response from GPT
        answer = response.choices[0].message.content
        
        return(answer)

    def returning_chatchat(self,messages):
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=1,
            max_tokens=2048,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
            response_format={
                "type": "text"
            },
            
            )
        answer = response.choices[0].message.content
        
        return(answer)
    def createCustomer(self):
        ...


if __name__ == "__main__":


    # Read the .ini file
    config = ConfigParser()
    config.read('config.ini')

    # Initialliaze OpenAI
    customer_agent = Bot(config['OPENAI']['APIKEY'])


    print(customer_agent.chat("Hey I am coming from France and I would like to stay at your house for the night"))