import asyncio
import datetime
import os

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.server_api import ServerApi
import httpx
import bs4  # beautifulsoup
import pandas as pd
import tqdm
import anyio


all_locations = {
    # "Arosa,Switzerland": "cceff603c7d427f8ef9796064a2d06cd63a10c26",
    # "Ayent,Switzerland": "eaf23c93ed2f83c2eae9fccfe58fedf55dfb475e",
    # "Bergun,Switzerland": "9748d7091a39018a7227963e7a0dde5c9bdb6713",
    # "Brissago,Switzerland": "b9868e42329b6cc5ea383fd2ba87eb4521d3c087",
    # "Buren_An_Der_Aare,Switzerland": "8650b0008f8dbb45e77293a306f24405d32e0436",
    # "Crans_Montana,Switzerland": "880996c8b58f8963956e2c9c30dfde90bf2279cc",
    # "Disentis,Switzerland": "1316c0d53b6879d06c5567a5f787c6e389645fef",
    # "Engelberg,Switzerland": "1c179d81d1a5cc28a42e5b25331d5ee9caf7d524",
    # "Flims,Switzerland": "97bdbdad92c771e797305c35422e74d669e38d13",
    # "Goldach,Switzerland": "fdad6691a94fb10b1ab79bf70f0a6aea4432b6a6",
    # "Gryon,Switzerland": "46fa2df08f8d9f4ff8f06e367353ff78dee04f85",
    # "Gstaad,Switzerland": "4bdf8176ad1fcece5619a8429271632fdfd97112",
    # "Koniz,Switzerland": "bf1e33af813d11bf1da9ded9590ebae6107dceb6",
    # "La_Sarraz,Switzerland": "ea650026d9bb0fcb6e5271600640bf5452cbf968",
    # "Meisterschwanden,Switzerland": "d0537b1d4b8ac9c3936a3b05ff73e719e20f9137",
    # "Oberhelfenschwil,Switzerland": "4e2e7eb09c39fbf0df04694b35aa99f364ac317d",
    # "Porrentruy,Switzerland": "00e2013c03f5508c05f97aa69555d1c17d5cd81d",
    # "Scuol,Switzerland": "b70002e6f328e9046c7dbce34b33828cf41209b0",
    # "Saint_Moritz,Switzerland": "d4d16cbf282c5ad0f71ba9b2bd7780ffda7f257d",
    # "Uster,Switzerland": "7e990ad1487f526fb6be985b43bdd1d50b06336c",
    # "Vernier,Switzerland": "1053dba5793f4bf4b161c735517f1872816de64e",
    # "Wildhaus,Switzerland": "dcee4105848e23dff73e4260554d653096547140",
    # "Yverdon,Switzerland": "42e5e747472654a826fd5ab96ff05d194002d7b1",

    "Aarau,Switzerland": "5a5ecc58df562835e3fcbae5f8c52e64e7247918",
    "Adelboden,Switzerland": "32fd88507fa3c9dc5351ba69e408507b44f37d4e",
    "Amriswil,Switzerland": "3d2affaab700ae926e9e7daf045849e1e03ba0c3",
    "Andermatt,Switzerland": "4fa4d953b6595a92f1c013fc4edd06da171b87a6",
    "Appenzell,Switzerland": "162a2967db482d9de5e1db7b98c7fa5a779f2875",
    "Ascona,Switzerland": "e17bca46ef6ffc22a36853d5432855480cd579d2",
    "Basel,Switzerland": "e502a0a8fc421e6a8f9f1c4034f6b46ff6f59f62",
    "Bellinzona,Switzerland": "f398035eff9921de0368cc494578468b1d5c99ad",
    "Bern,Switzerland": "94fa2a5396a4723b31142ab413d3ec1be77d62d8",
    "Biel,Switzerland": "a6d41fac1a5c23907b50d10a3c2610ffba7e63ed",
    "Brienz,Switzerland": "cd694dbb044fbf6104cff9d3d15b8a8ea4a65b79",
    "Bulle,Switzerland": "b9cae3e5aed5e65e8c60067a2c357621cc009e51",
    "Chur,Switzerland": "6c0da286ee836415b66b138d6f13076fbcdb3899",
    "Davos,Switzerland": "e260b1b791f27abac6a4f7771a2401be6aee67a9",
    "Delemont,Switzerland": "f661d8d34fbb2431d6f02a9613c09a3782655d55",
    "Einsiedeln,Switzerland": "14ee1f6a8ff571616de7f378af94b0a588c67bda",
    "Emmen,Switzerland": "910f599ec7efe9797484a60e58c1ae25cced9e86",
    "Fortunau,Switzerland": "867c0c46130727841ae510748b23d13f5baf0e17",
    "Frauenfeld,Switzerland": "8bf573628b0fd96382f03bef84c063f3aa481e21",
    "Fribourg,Switzerland": "f5240fc4fcffbe2c1680ee6f026349a7c2c0da48",
    "Geneva,Switzerland": "eacb20159164fa15c55f87d7d66068b4b2ceaf39",
    "Glarus,Switzerland": "dcb4a71fe438a4165ee26a4d370d259a2c5896d0",
    "Grindelwald,Switzerland": "ab1c057337ed2fca115ed0e16b4ec2467466aaad",
    "Ilanz,Switzerland": "4e7515526f98bbd07d6495d2c57936580fbabd57",
    "Interlaken,Switzerland": "79dd56d026119e05406ee521078bf148ca22d7ca",
    "Kandersteg,Switzerland": "476d318ef8a04cc3d660457f705ee35c811b9ca4",
    "Kreuzlingen,Switzerland": "6df313894b577833016e41b126659862499eb441",
    "La_Chaux_De_Fonds,Switzerland": "d78dc7da556213f33175d58cc6d1de8534ac3a6c",
    "Laax,Switzerland": "eb8dfc2322338b344ef7f8f1063e01f91b555137",
    "Lausanne,Switzerland": "fb15d1e5d748ce024a944f59f9bf651919032bd1",
    "Lauterbrunnen,Switzerland": "8a9e5db01b10728c85ac4944d19e79e515f3deba",
    "Lenzerheide,Switzerland": "73330944ee4dbe329e5f8cfbf7bc49a0f420ba2f",
    "Leukerbad,Switzerland": "7d2f2e013101f38faf031a38c5d9b348aeb883e3",
    "Locarno,Switzerland": "e2989e0d045612b8bbd9de7d3fa408c5b4429541",
    "Lucerne,Switzerland": "470964fac0430b6083c52ddd3e2a400c542e0e60",
    "Lugano,Switzerland": "f9bc6e13323ac7547a608fa227ff7e274284d1f2",
    "Martigny,Switzerland": "5db7a964aacd91333598abd6c251657e68e67663",
    "Melide,Switzerland": "fe52462ca74ec5a9ec29bb4fff7e534b653a0902",
    "Montreux,Switzerland": "0034c59b5b977acd17fe5837e5845ae9f41e5a09",
    "Murren,Switzerland": "49112aabb5de822694504ee63c3a2e87a290e815",
    "Murten,Switzerland": "6eb04bd95e05c180215293c5aaaa2cf5743c1c5b",
    "Nendaz,Switzerland": "91ebe8de8fcbcd36d45877be09019bd31414d1bc",
    "Neuchatel,Switzerland": "684590561854da6d27a36d9e659cc4739f675b1c",
    "Orselina,Switzerland": "7e8862320a0714b3c7ee0201dea67f3d88ad349f",
    "Payerne,Switzerland": "e1a073c91cf80e72b3535b2d1b274ec274f1a3e3",
    "Piazzogna,Switzerland": "3b72a854add1c56cbc7ed93321cf4d4a1061d399",
    "Pontresina,Switzerland": "e8f8d4d08d7cd2a4121fc88d0030d26fd98300de",
    "Poschiavo,Switzerland": "cc861a51e98cea87f7cd71b735baa9afd571a8c1",
    "Rapperswil,Switzerland": "e296f4a4b599b329b9472c1a785c634631ca1006",
    "Romanshorn,Switzerland": "39fe927062dc9f07e6b3abed0189caf29b9745fd",
    "Saas_Fee,Switzerland": "865c64f03112f377ad70f301a218110eefa322b8",
    "Samaden,Switzerland": "7b8de7f102899b53066053f1f633c0b82f51f426",
    "Samnaun,Switzerland": "f43f594fb873470e23c7fc09603a4978ad28c8df",
    "Sarnen,Switzerland": "8a7c9fe3ae4cbce26ca0d3447542641f60ef781c",
    "Savognin,Switzerland": "8bb604df8ccd428e2f37e5c4239c93f4dc55f19f",
    "Schaffhausen,Switzerland": "8b5f38ff71ef8dcc2b857f39361149bb6193e4c3",
    "Schwarzsee,Switzerland": "3bb733057180992f95dac64313f95ba8f6008e98",
    "Sion,Switzerland": "f092059ab917cc1a9a335215a1f4744944feaec3",
    "Solothurn,Switzerland": "a6e3ca1b9fedf679fcc41159f5f5a56a58ca7354",
    "St_Gallen,Switzerland": "c6a7895be45659cd932d951b975b522d5964f9af",
    "Stein_Am_Rhein,Switzerland": "1ce24b9cf847e95318b40d6bce54deb78052155d",
    "Tenero,Switzerland": "cb4313847fec5d64e08e0549340a914da569db0f",
    "Thun,Switzerland": "4e567234358d307fb77c5cb5514150df3cd59a3c",
    "Trient,Switzerland": "4129b87c07a38beede842f89d10f363648f6089c",
    "Verbier,Switzerland": "d9ab4f99f16929d6a5dea4a9b3f20d60af8dd3f9",
    "Vevey,Switzerland": "19283b9186e4a90e95159fa3c857e78aae5eef6d",
    "Veysonnaz,Switzerland": "24f637145c5606fb31e88a5f72dc7a89cb3a7b49",
    "Visp,Switzerland": "783420cf10c47747d87a98078efc15ee7924ce07",
    "Wengen,Switzerland": "bfd1bd4f3fdc83872749b9b33f9fe9f87added62",
    "Winterthur,Switzerland": "0653a595aa782c15a960e2850b10b76f86f5939e",
    "Zermatt,Switzerland": "b165a59a6f441aa227744995430abf0d32530c3b",
    "Zweisimmen,Switzerland": "94d9af7f3f88b1f06e944301ae4b886ccf7b12dd",
    "Zurich,Switzerland": "be1ac363913afba07be684e70dcbb7b7dcfd2ba1",
}


async def access_the_website(location, authority, month, day):
    """Accesse the website with the needed parameters; returns a json-document"""
    
    async with httpx.AsyncClient(
        base_url="https://www.wetter2.com/v1/",
    ) as client:
        res = await client.post(
            url="past-weather/",
            data={
                "place": location,
                "day": day,
                "month": month,
                "city": location.split(',')[0].replace('_', ' '),
                "country": location.split(',')[1],              
            },
            headers={
                "X-Requested-With": "XMLHttpRequest",
                "authority": authority,
            },
        )
        res.raise_for_status()
        res_json = res.json()
    
    return res_json
    

async def prepare_the_data(location, authority, year, month, day):
    """Select the interesting data from the json-document and create a pandas-dataFrame;
    return a pandas-dataFrame with the location-, time- and weather-data"""
    
    res_json = await access_the_website(location, authority, month, day)
    res_years = res_json['data']['years']
    
    if not isinstance(res_years, dict):
        raise ValueError(f"Cannot parse data for {day=} {month=}: {str(res_years)[:50]}...")

    results = []
        
    for k, v in res_years.items():
        date = datetime.date(year=year, day=day, month=month)
    
        res_table = v['table']

        soup = bs4.BeautifulSoup(res_table)  # bs4 makes the html more readable

        # Head of the table contains the times
        head = soup.table.thead

        # Creates a list of all the times found on the website
        timestamps = []
        for td in head.find_all("td"):
            dt = datetime.datetime.combine(date, datetime.time.fromisoformat(td.text))
            dt = pd.Timestamp(dt).tz_localize("UTC")
            timestamps.append(dt)

        # Create a Pandas-DataFrame with the Indexes 'timestamp' and 'location' and the data of the dict
        index = pd.MultiIndex.from_frame(pd.DataFrame(data={"location": location, "datetime": timestamps}))
        
        # Body of the table contains the data
        body = soup.table.tbody

        # for temperature and wind, the data can be found in the html-tag 'span class'
        # (with dot-notation instead of comma like in the innerHTML);
        # rain and cloud_percentage are only in the innerHTML, so they are found by the <td> around them
        data = dict(
            temp_C=[
                float(span["data-temp"])
                for span in body.find("th", text="Temperatur").parent.find_all("span", class_="day_temp")
            ],
            rain_mm=[
                float(td.find("span", class_=lambda c:not c).text.replace(",", "."))
                for td in body.find("th", text="Niederschlag").parent.find_all("td")
            ],
            wind_kmh=[
                float(span["data-wind"])
                for span in body.find("th", text="Wind").parent.find_all("span", class_="day_wind")
            ],
            cloud_percent=[
                # no percentage-symbol, instead of , we need dots for decimals
                float(td.text.replace(",", ".").rstrip('%'))
                for td in body.find("th", text="Wolkendecke").parent.find_all("td")
            ],
        )
    
        result = pd.DataFrame(data=data, index=index)
        
        results.append(result)
    
    df_results = pd.concat(results)  # all result-DataFrame are combined to one DataFrame
    
    return df_results


async def insert_data_in_db(collection, data):
    """Insert the data to the collection; if there is already a data-set with the same location and time, 
    the old data is overwritten"""
    
    data = data.reset_index().to_dict("records")
    for d in data:
        await collection.replace_one(
            dict(
                location=d["location"],
                datetime=d["datetime"],
            ),
            d,
            upsert=True,
        )

        
async def handle_run_the_program(receive_stream, collection):
    """Handel parallel-processes for the functions prepare_the_data() and insert_data_in_DB()"""
    
    async with receive_stream:
        async for location, authority, year, base_date in receive_stream:
            day = base_date.day
            month = base_date.month
            try:
                data = await prepare_the_data(location, authority, year, month, day)
                await insert_data_in_db(collection, data)

            except Exception as ex:
                print(f"{location} / {base_date:%m-%d} failed: {ex!r}")


async def run_the_program(collection, locations, year, start_date, end_date):
    """Run all the above methods"""
        
    send_stream, receive_stream = anyio.create_memory_object_stream()
    
    location_range = tqdm.tqdm(locations.items())

    async with anyio.create_task_group() as task_group:
        
        for _ in range(4):
            task_group.start_soon(
                handle_run_the_program, 
                receive_stream.clone(),
                collection
            )
        receive_stream.close()
        async with send_stream:            
    
            for k, v in location_range:
                location = k
                authority = v
                location_range.set_description(location)

                # we only need the month and day of this date_range;
                date_range = tqdm.tqdm(
                    pd.date_range(start_date, end_date, freq="D"),
                    leave=False,
                )

                for base_date in date_range:
                    date_range.set_description(f"{base_date:%m-%d}")
                    await send_stream.send((location, authority, year, base_date))
                    

async def main():
    uri = os.environ['MONGODB_URI']
    DBclient = AsyncIOMotorClient(uri, server_api=ServerApi('1'))
    db = DBclient.data
    collection = db.wetter2

    end_date = datetime.date.today()
    start_date = end_date - datetime.timedelta(days=3)
    year = end_date.year
    
    await run_the_program(
        collection=collection,
        locations=all_locations,
        year=year,
        start_date=start_date,
        end_date=end_date,
    )


if __name__ == "__main__":
    asyncio.run(main())
