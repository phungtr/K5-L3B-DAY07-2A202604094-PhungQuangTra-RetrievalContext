# Phiếu chấm agent — test

Thang: answer_grade 0 = sai/thiếu evidence/từ chối câu có đáp án; 1 = đúng một phần; 2 = đúng và đủ, citation hỗ trợ mọi ý. citation_support: từng citation có thực sự hỗ trợ câu trả lời không. Câu thiếu evidence: abstention_correct = agent từ chối và không thêm khẳng định vô căn cứ.

## t01 · dien_dat_lai · filter=None

**Q:** How many net new manufacturing jobs did Vietnam add over the past three years, and in what kind of sectors were these jobs mainly created?

**Expected:** About 1.6 million net new manufacturing jobs, created mainly in export-oriented sectors (such as textiles and electronics).  
- gold[A] ts-2017-12 p18: "Over the past three years Vietnam added 1.6 million new manufacturing jobs (net) - a significant pick up in manufacturing job creation. Within manufacturing, jobs were primarily created in export orie"
- gold[A] ts-2017-12 p11: "Over the last three years, Vietnam added 1.6 million new manufacturing jobs (net), especially in export-oriented sectors."

### `t01|650b79f7` ← A0_dense_k3_b800
- status: **abstain**, searches: ['net new manufacturing jobs Vietnam past three years sectors created', 'net new manufacturing jobs Vietnam added past three years sectors', 'Vietnam manufacturing jobs added sectors 2015 2016 2017 2018']
- answer: There is no evidence in the reports regarding the number of net new manufacturing jobs added by Vietnam over the past three years or the sectors in which these jobs were created.

### `t01|1b2f8dc4` ← A4_dense_rerank_k5_b4000_repair
- status: **answered**, searches: ['net new manufacturing jobs Vietnam past three years sectors created']
- answer: Over the past three years, Vietnam added 1.6 million net new manufacturing jobs, primarily in export-oriented sectors such as textiles and electronics. Additionally, the construction, retail, and hospitality sectors contributed another 700,000 jobs, with these four sectors together accounting for 80 percent of all jobs created during this period [ts-2017-12:p018:para:001][ts-2017-12:p011:para:004].
- gợi ý: ý đáp án [True, True], context đủ evidence=True
  - [ts-2017-12:p018:para:001] gold-group=['A']: 1.8. The economic recovery over the past three years was associated with a pick-up in job creation, especially in manufacturing. Over the past three years Vietnam added 1.6 million new manufacturing jobs (net) - a significant pick up in manufacturing job creation. Within manufacturing, jobs were primarily created in export oriented sectors i.e. textiles and electronics. Labor demand in construction, retail and hospitality sectors was also buoyant with these sectors together adding another 700,000 jobs. These four sectors together accounted for 80 percent of all jobs created, with the manufacturing sector contributing to more than half of all new jobs between 2014 and 2016. They absorbed labo
  - [ts-2017-12:p011:para:004] gold-group=['A']: Vietnam's dynamic economy continues to create jobs and rapid real wage growth, leading to broad-based welfare gains and poverty reduction. Real disposable household incomes are benefiting from low inflation, an expanding wage sector, and a robust nominal wage growth. Over the last three years, Vietnam added 1.6 million new manufacturing jobs (net), especially in export-oriented sectors. Labor demand in construction, retail, and hospitality sectors was also buoyant, with these sectors together adding another 700,000 jobs. Strong job creation helped reinvigorate structural transformation and reallocation of labor to higher-productivity activities, thereby boosting aggregate labor productivity.

## t02 · dien_dat_lai · filter=None

**Q:** How fast did average wages in Vietnam's public sector grow compared with the domestic and FDI private sector between Q1 2014 and Q1 2017, and what explains the difference?

**Expected:** Public-sector wages grew only about 3 percent on average, versus about 8.4 percent in the domestic and FDI private sector, reflecting the government's efforts to rein in the public-sector wage bill.  
- gold[A] ts-2017-12 p19: "Average monthly nominal wages in the domestic and FDI private sector grew rapidly expanding at an average rate of 8.4 percent. Meanwhile wages in the public sector grew only by an average 3 percent, r"

### `t02|2a18db24` ← A0_dense_k3_b800
- status: **abstain**, searches: ['average wages Vietnam public sector growth domestic FDI private sector Q1 2014 Q1 2017', 'average wages Vietnam public sector growth domestic FDI private sector Q1 2014 Q1 2017 comparison explanation', 'Vietnam public sector average wages growth domestic private sector FDI Q1 2014 Q1 2017 comparison explanation']
- answer: There is no evidence in the reports regarding the growth rates of average wages in Vietnam's public sector compared to the domestic and FDI private sectors between Q1 2014 and Q1 2017, nor any explanation for potential differences.

### `t02|294874b0` ← A4_dense_rerank_k5_b4000_repair
- status: **answered**, searches: ['average wages Vietnam public sector growth domestic FDI private sector Q1 2014 Q1 2017', 'average wages Vietnam public sector growth domestic FDI private sector explanation Q1 2014 Q1 2017', 'average wages Vietnam public sector growth domestic FDI private sector comparison Q1 2014 Q1 2017', 'average wages Vietnam public sector growth domestic FDI private sector Q1 2014 Q1 2017 explanation']
- answer: Between Q1 2014 and Q1 2017, average nominal wages in Vietnam's public sector grew by only 3%, while wages in the domestic and FDI private sectors grew at a faster rate of 8.4%. This difference is attributed to the government's efforts to control the public-sector wage bill, despite strong labor demand and wage growth in the private sectors driven by robust economic conditions and job creation in various industries [ts-2017-12:p019:para:000][ts-2017-12:p011:para:004].
- gợi ý: ý đáp án [True, True, True], context đủ evidence=True
  - [ts-2017-12:p019:para:000] gold-group=['A']: Figure 1.6: net employment creation by sector,
Figure 1.7: Manufacturing output and Employment growth (%)
1.9. strong labor demand also lifted real wages. Average nominal wages increased by 8 percent on average between Q1 2014 and Q1 2017. Average monthly nominal wages in the domestic and FDI private sector grew rapidly expanding at an average rate of 8.4 percent. Meanwhile wages in the public sector grew only by an average 3 percent, reflecting the government's efforts in reining in the public-sector wage bill. Wages grew in all sectors but expanded fastest in industry where demand for labor was strongest. High wage growth in both the domestic and FDI sector and across all industries, under
  - [ts-2017-12:p011:para:004] gold-group=-: Vietnam's dynamic economy continues to create jobs and rapid real wage growth, leading to broad-based welfare gains and poverty reduction. Real disposable household incomes are benefiting from low inflation, an expanding wage sector, and a robust nominal wage growth. Over the last three years, Vietnam added 1.6 million new manufacturing jobs (net), especially in export-oriented sectors. Labor demand in construction, retail, and hospitality sectors was also buoyant, with these sectors together adding another 700,000 jobs. Strong job creation helped reinvigorate structural transformation and reallocation of labor to higher-productivity activities, thereby boosting aggregate labor productivity.

## t03 · metadata_filter · filter={'edition': '2017-12'}

**Q:** According to the December 2017 Taking Stock report, how did the State Bank of Vietnam change its rediscount and refinancing rates in July 2017?

**Expected:** It cut both rates by 25 basis points, to 4.25 percent (rediscount) and 6.25 percent (refinancing), its first rate adjustment in three years.  
- gold[A] ts-2017-12 p22: "cutting its rediscount rate and refinancing rate by 25 basis points to 4.25 and 6.25 percent respectively"
- gold[A] ts-2017-12 p10: "cut its rediscount rate and refinancing rate by 25 basis points to 4.25 and 6.25 percent respectively"

### `t03|a428e0ed` ← A0_dense_k3_b800
- status: **abstain**, searches: ['State Bank of Vietnam rediscount refinancing rates July 2017', 'State Bank of Vietnam July 2017 monetary policy changes', 'State Bank of Vietnam monetary policy July 2017 changes rediscount refinancing rates', 'State Bank of Vietnam July 2017 rediscount refinancing rates changes']
- answer: The evidence regarding changes made by the State Bank of Vietnam to its rediscount and refinancing rates in July 2017 is missing from the provided passages.

### `t03|11eb9bd6` ← A4_dense_rerank_k5_b4000_repair
- status: **answered**, searches: ['State Bank of Vietnam rediscount refinancing rates July 2017']
- answer: In July 2017, the State Bank of Vietnam cut its rediscount rate and refinancing rate by 25 basis points to 4.25 percent and 6.25 percent respectively. This was the first rate adjustment in three years, aimed at easing the monetary policy stance to support economic growth amidst subdued price pressures and moderate inflation [ts-2017-12:p022:para:001][ts-2017-12:p010:para:002].
- gợi ý: ý đáp án [True, True, True], context đủ evidence=True
  - [ts-2017-12:p022:para:001] gold-group=['A']: 1.14. amidst subdued price pressures, the authorities have proactively eased the monetary policy stance to support economic growth. With moderate inflation, the State Bank of Vietnam in July eased monetary stance, cutting its rediscount rate and refinancing rate by 25 basis points to 4.25 and 6.25 percent respectively - first rate adjustment in three years. Accommodative monetary policy contributed to easy liquidity conditions in the banking sector with interbank rates at less than one percent - significantly below historically low policy rates. Credit expansion remained elevated at around 18.5 percent (y/y) in October 2017, almost double nominal GDP growth. While credit expansion may be dri
  - [ts-2017-12:p010:para:002] gold-group=['A']: amidst muted price pressures, monetary and credit policies continued to balance stability and growth objectives. Headline CPI remains moderate at 3.0 percent (y/y) with stable underlying core inflation of 1.3 percent (y/y) in October. Taking advantage of subdued inflation, the State Bank of Vietnam in July cut its rediscount rate and refinancing rate by 25 basis points to 4.25 and 6.25 percent respectively. Credit growth remained elevated at around 18.5 percent (y/y) in October 2017. Such rapid credit expansion, especially if driven by administrative targets as opposed to economic fundamentals, may induce excessive risk taking and poor credit allocation and lead to associated deterioration i

## t04 · ngoai_le · filter=None

**Q:** What share of outstanding loans did Vietnam officially report as non-performing in December 2017, and what is the estimated share once NPLs held by VAMC and potential bad debts are included?

**Expected:** Officially about 2.3 percent of total outstanding loans (December 2017); about 7.36 percent once VAMC's NPLs and potential bad debts are included.  
- gold[A] ts-2018-06 p22: "NPLs in the banking system are officially reported equivalent to 2.3 percent of total outstanding loans of the banking sector as of December 2017, however, this only partly reflects asset quality chal"

### `t04|753ead16` ← A0_dense_k3_b800
- status: **abstain**, searches: ['Vietnam non-performing loans December 2017 share reported VAMC bad debts', 'Vietnam non-performing loans December 2017 official report share VAMC bad debts included', 'Vietnam non-performing loans December 2017 share reported VAMC bad debts included']
- answer: The evidence does not provide the official share of outstanding loans reported as non-performing in December 2017, nor the estimated share including NPLs held by VAMC and potential bad debts.

### `t04|63a87f59` ← A4_dense_rerank_k5_b4000_repair
- status: **answered**, searches: ['Vietnam non-performing loans December 2017 share reported VAMC bad debts']
- answer: Vietnam officially reported non-performing loans (NPLs) as 2.3 percent of total outstanding loans in December 2017. However, when including NPLs held by the Vietnam Asset Management Company (VAMC) and potential bad debts, the estimated total non-performing assets in the banking system rise to about 7.36 percent [ts-2018-06:p022:para:000].
- gợi ý: ý đáp án [True, True], context đủ evidence=True
  - [ts-2018-06:p022:para:000] gold-group=['A']: 11. Resolving remaining asset quality problems in the banking sector remains a priority. A major step in resolving the NPLs in the banking system was the National Assembly's Resolution 42 (effective from August 2017) that granted the Vietnam Asset Management Company (VAMC) more powers to resolve NPLs. The resolution allows banks to process pledged assets if the borrower in question is not co-operating, filling previous regulatory gaps. NPLs in the banking system are officially reported equivalent to 2.3 percent of total outstanding loans of the banking sector as of December 2017, however, this only partly reflects asset quality challenges in the banking system, as the measure does not includ

## t05 · ngoai_le · filter=None

**Q:** Why did Vietnam's oil export earnings fall in the first four months of 2018 even though oil prices were higher?

**Expected:** Because export volumes declined substantially: oil production is constrained by technical capacity limits of Vietnam's maturing oil fields. Although oil prices rose 26.3 percent (y/y), oil export earnings contracted by 27 percent.  
- gold[A] ts-2018-06 p22: "Oil production and hence exports continue to be constrained by technical capacity constraints related to Vietnam's maturing oil fields. While oil prices are up by 26.3 percent (y/y), a substantial dec"

### `t05|43c11570` ← A0_dense_k3_b800
- status: **abstain**, searches: ['Vietnam oil export earnings fall first four months 2018 reasons', 'Vietnam oil export earnings decline first four months 2018 despite higher prices', 'Vietnam oil export earnings fall first four months 2018 despite higher prices reasons']
- answer: The evidence does not provide specific reasons for the fall in Vietnam's oil export earnings in the first four months of 2018 despite higher oil prices. Details regarding the volume of oil exports or other contributing factors are missing.

### `t05|8873be67` ← A4_dense_rerank_k5_b4000_repair
- status: **answered**, searches: ['Vietnam oil export earnings fall first four months 2018 reasons']
- answer: Vietnam's oil export earnings fell in the first four months of 2018 despite higher oil prices due to a substantial decline in export volumes, which was constrained by technical capacity issues related to maturing oil fields. Specifically, while oil prices increased by 26.3 percent year-on-year, the overall oil export earnings contracted by 27 percent during this period due to these volume declines [ts-2018-06:p022:para:003].
- gợi ý: ý đáp án [True, True, True], context đủ evidence=True
  - [ts-2018-06:p022:para:003] gold-group=['A']: 13. Agricultural exports also continued to expand with increasingly diversified underlying export basket and a move into higher value crops. Exports of agriculture products also continued to expand driven by rice, cashew, coffee, fisheries, and vegetables and fruits. Importantly, Vietnam continues to diversify its agricultural exports to higher value crops, including vegetables and fruits which surged 42 percent in 2017 and 29 percent in 4M-2018. The export value of vegetables and fruits has now surpassed export earnings from traditional commodities, such as crude oil, rice and black pepper.
14. Meanwhile, oil exports declined despite rising oil prices. Oil production and hence exports conti

## t06 · dien_dat_lai · filter=None

**Q:** How old is Vietnam's active trucking fleet on average compared with Australia's, and what share of truck miles are driven empty?

**Expected:** About 17 years on average versus 14 years in Australia; about 35 percent of truck miles are empty (World Bank study, 2010).  
- gold[A] ts-2018-06 p50: "about 35 percent of truck miles are empty according to a World Bank study in 2010, and the average age of Vietnam's active trucking fleet is 17 years, much greater than 14 years in Australia"

### `t06|a8642070` ← A0_dense_k3_b800, A4_dense_rerank_k5_b4000_repair
- status: **answered**, searches: ['average age of trucking fleet Vietnam Australia empty truck miles share']
- answer: Vietnam's active trucking fleet has an average age of 17 years, compared to 14 years in Australia. Additionally, about 35 percent of truck miles in Vietnam are driven empty [ts-2018-06:p050:para:001].
- gợi ý: ý đáp án [True, True, True], context đủ evidence=True
  - [ts-2018-06:p050:para:001] gold-group=['A']: Trucking industry, the largest asset-based LSP , faces a significant efficiency gap: about 35 percent of truck miles are empty according to a World Bank study in 2010, and the average age of Vietnam's active trucking fleet is 17 years, much greater than 14 years in Australia, 9 years in Canada and Japan, 8 years in the U.K., and 6-6.5 years in U.S. and France. Similar is true for inland waterway sector: the average barge size in Vietnam is at 100 deadweight tons, minuscule compared to 2,400 tons in Western Europe with well-developed waterway transport sector, due to the lack of ability to invest and grow, largely limited by access to capital.

## t07 · truc_tiep · filter=None

**Q:** According to 2010 claims data from the Vietnam Social Security Fund, how much did procurement prices for the same drug vary across public hospitals?

**Expected:** There was up to a fivefold difference in procurement prices for the same drug across public hospitals.  
- gold[A] ts-2017-12 p46: "claims data from the Vietnam Social Security Fund (VSSF) in 2010 indicated up to a fivefold difference in procurement prices for the same drug across public hospitals."

### `t07|42402f47` ← A0_dense_k3_b800
- status: **answered**, searches: ['2010 claims data Vietnam Social Security Fund procurement prices drug public hospitals']
- answer: According to 2010 claims data from the Vietnam Social Security Fund, procurement prices for the same drug varied by up to fivefold across public hospitals due to decentralized procurement practices. This information is from the December 2017 edition of the report [ts-2017-12:p046:para:000].
- gợi ý: ý đáp án [True], context đủ evidence=True
  - [ts-2017-12:p046:para:000] gold-group=['A']: comprise 60 percent of total reimbursements from health insurance. Decentralized procurement has led to a variation in prices across provinces. For instance, claims data from the Vietnam Social Security Fund (VSSF) in 2010 indicated up to a fivefold difference in procurement prices for the same drug across public hospitals.

### `t07|f9c191c3` ← A4_dense_rerank_k5_b4000_repair
- status: **answered**, searches: ['2010 claims data Vietnam Social Security Fund procurement prices drug public hospitals']
- answer: According to the 2010 claims data from the Vietnam Social Security Fund, procurement prices for the same drug varied by up to fivefold across public hospitals [ts-2017-12:p046:para:000].
- gợi ý: ý đáp án [True], context đủ evidence=True
  - [ts-2017-12:p046:para:000] gold-group=['A']: comprise 60 percent of total reimbursements from health insurance. Decentralized procurement has led to a variation in prices across provinces. For instance, claims data from the Vietnam Social Security Fund (VSSF) in 2010 indicated up to a fivefold difference in procurement prices for the same drug across public hospitals.

## t08 · metadata_filter · filter={'edition': '2018-06'}

**Q:** According to the June 2018 Taking Stock report, how much foreign direct investment did foreign investors disburse in Vietnam in 2017?

**Expected:** A record US$17.5 billion.  
- gold[A] ts-2018-06 p26: "In 2017, foreign investors disbursed a record US$17.5 billion to Vietnam"

### `t08|646bf6ea` ← A0_dense_k3_b800
- status: **abstain**, searches: ['foreign direct investment disbursed Vietnam 2017', 'foreign direct investment Vietnam 2017 total disbursement', 'foreign direct investment disbursement Vietnam 2017 total', 'foreign direct investment disbursement Vietnam 2017 total amount']
- answer: The evidence does not provide the total amount of foreign direct investment disbursed by foreign investors in Vietnam for the year 2017 as requested.

### `t08|9b92475f` ← A4_dense_rerank_k5_b4000_repair
- status: **answered**, searches: ['foreign direct investment disbursed Vietnam 2017']
- answer: In 2017, foreign investors disbursed a record US$17.5 billion to Vietnam across a broad and diversified range of investment activities [ts-2018-06:p026:para:001].
- gợi ý: ý đáp án [True], context đủ evidence=True
  - [ts-2018-06:p026:para:001] gold-group=['A']: 19. Reflecting positive investor sentiment, foreign direct investment inflows accelerated in 2017 and in the first quarter of 2018. Recently concluded trade agreements-such as the Comprehensive and Progressive Trans-Pacific Partnership (CPTPP) and EU Vietnam Free Trade Agreement (EV-FTA)- have further boosted investor confidence and helped usher in sustained FDI inflows. In 2017, foreign investors disbursed a record US$17.5 billion to Vietnam across a broad and diversified range of investment activities. In the first quarter of 2018, FDI disbursement were sustained at the 7.2 percent growth rate achieved over the same period in 2017. Currently, the foreign-invested sector contributes about a

## t09 · dien_dat_lai · filter=None

**Q:** How unevenly is Vietnam's national budget revenue distributed across provinces?

**Expected:** Very unevenly: about 80 percent of national budget revenue is concentrated in a quarter of the provinces.  
- gold[A] ts-2017-12 p53: "about 80 percent of the national budget revenue is concentrated in a quarter of provinces"

### `t09|e5629988` ← A0_dense_k3_b800
- status: **answered**, searches: ['Vietnam national budget revenue distribution across provinces']
- answer: Vietnam's national budget revenue is unevenly distributed across provinces, with about 80 percent of the national budget revenue concentrated in a quarter of the provinces. However, the fiscal transfer system helps poorer provinces make progress in socio-economic development despite this uneven distribution [ts-2017-12:p053:para:001].
- gợi ý: ý đáp án [True, True], context đủ evidence=True
  - [ts-2017-12:p053:para:001] gold-group=['A']: Under these arrangements, although budget revenues are not distributed evenly across provinces (about 80 percent of the national budget revenue is concentrated in a quarter of provinces), the allocation of budget expenditure ensures that poorer provinces are resourceful in making apparent progress in socio-economic development due to the fiscal transfer system.

### `t09|1bd2c762` ← A4_dense_rerank_k5_b4000_repair
- status: **answered**, searches: ['Vietnam national budget revenue distribution across provinces', 'Vietnam national budget revenue uneven distribution provinces', 'Vietnam national budget revenue concentration provinces', 'Vietnam national budget revenue distribution provinces 2018']
- answer: Vietnam's national budget revenue is unevenly distributed across provinces, with about 80 percent of the national budget revenue concentrated in a quarter of the provinces. However, the fiscal transfer system helps poorer provinces make progress in socio-economic development despite this concentration of revenue [ts-2017-12:p053:para:001].
- gợi ý: ý đáp án [True, True], context đủ evidence=True
  - [ts-2017-12:p053:para:001] gold-group=['A']: Under these arrangements, although budget revenues are not distributed evenly across provinces (about 80 percent of the national budget revenue is concentrated in a quarter of provinces), the allocation of budget expenditure ensures that poorer provinces are resourceful in making apparent progress in socio-economic development due to the fiscal transfer system.

## t10 · multi_hop · filter=None

**Q:** How did Vietnam's year-on-year credit growth reported for October 2017 in the December 2017 Taking Stock report compare with the year-on-year rate estimated for the first quarter of 2018 in the June 2018 report?

**Expected:** About 18.5 percent (y/y) in October 2017 versus about 14 percent (y/y, nominal) in the first quarter of 2018: credit growth slowed but remained elevated.  
- gold[A] ts-2017-12 p22: "Credit expansion remained elevated at around 18.5 percent (y/y) in October 2017"
- gold[A] ts-2017-12 p10: "Credit growth remained elevated at around 18.5 percent (y/y) in October 2017"
- gold[B] ts-2018-06 p21: "equivalent to about 14 percent year-on-year in nominal terms"

### `t10|8bf09c4e` ← A0_dense_k3_b800
- status: **abstain**, searches: ['Vietnam year-on-year credit growth October 2017 December 2017 Taking Stock report', 'Vietnam year-on-year credit growth first quarter 2018 June 2018 Taking Stock report', 'Vietnam year-on-year credit growth October 2017']
- answer: The evidence for Vietnam's year-on-year credit growth for October 2017 and the estimated rate for the first quarter of 2018 is missing from the provided passages.

### `t10|82b69eca` ← A4_dense_rerank_k5_b4000_repair
- status: **answered**, searches: ['Vietnam year-on-year credit growth October 2017 December 2017 Taking Stock report', 'Vietnam year-on-year credit growth first quarter 2018 June 2018 Taking Stock report', 'Vietnam year-on-year credit growth October 2017', 'Vietnam credit growth October 2017 year-on-year December 2017 Taking Stock report']
- answer: In October 2017, Vietnam's year-on-year credit growth was reported at around 18.5 percent in the December 2017 report [ts-2017-12:p010:para:002]. In contrast, the June 2018 report estimated the year-on-year credit growth for the first quarter of 2018 to be about 14 percent [ts-2018-06:p021:para:001].
- gợi ý: ý đáp án [True, True], context đủ evidence=True
  - [ts-2017-12:p010:para:002] gold-group=['A']: amidst muted price pressures, monetary and credit policies continued to balance stability and growth objectives. Headline CPI remains moderate at 3.0 percent (y/y) with stable underlying core inflation of 1.3 percent (y/y) in October. Taking advantage of subdued inflation, the State Bank of Vietnam in July cut its rediscount rate and refinancing rate by 25 basis points to 4.25 and 6.25 percent respectively. Credit growth remained elevated at around 18.5 percent (y/y) in October 2017. Such rapid credit expansion, especially if driven by administrative targets as opposed to economic fundamentals, may induce excessive risk taking and poor credit allocation and lead to associated deterioration i
  - [ts-2018-06:p021:para:001] gold-group=['B']: 10. Despite a slight deceleration in the first quarter 2018, credit growth remains elevated. Total banking sector lending is estimated to expand 3.6 percent (year-to-date) in the first quarter of 2018 - equivalent to about 14 percent year-on-year in nominal terms, below the estimate of 18.2 percent cumulative credit growth in 2017 (figure 17). Vietnam credit cycle stands out from trends in most other countries of the region, including China, which have seen gradual tightening. Vietnam's overall credit to GDP is also relatively high - at about 130 percent of GDP in December 2017, and credit is expanding at around 1.4 times the growth rate of nominal GDP . This rapid pace of credit growth may 

## t11 · multi_hop · filter=None

**Q:** Compare Vietnam's merchandise export growth in January-October 2017, as reported in the December 2017 Taking Stock report, with export growth over the first four months of 2018 reported in the June 2018 report.

**Expected:** Exports grew 21.3 percent (y/y) in January-October 2017, to about US$174.5 billion, versus 19.2 percent (y/y, value terms) in the first four months of 2018.  
- gold[A] ts-2017-12 p23: "Vietnam's total export turnover between January and October 2017 is estimated at $174.5 billion, up 21.3 percent from the same period last year."
- gold[A] ts-2017-12 p10: "export turnover reached US$174.5 billion (about 86 percent of GDP) in the first 10 months of 2017, up 21.3 percent from the same period last year"
- gold[B] ts-2018-06 p22: "Over the first four months of 2018, Vietnamese export growth accelerated 19.2 percent in value terms (y/y)."

### `t11|e264ba99` ← A0_dense_k3_b800
- status: **abstain**, searches: ['Vietnam merchandise export growth January-October 2017 December 2017 Taking Stock report', 'Vietnam merchandise export growth first four months 2018 June 2018 Taking Stock report']
- answer: The evidence for Vietnam's merchandise export growth in the first four months of 2018 is missing from the reports. Only the growth for January-October 2017 is available, which is 21.3 percent, but there is no data for the specified period in 2018.

### `t11|4ea7e286` ← A4_dense_rerank_k5_b4000_repair
- status: **answered**, searches: ['Vietnam merchandise export growth January-October 2017 December 2017 Taking Stock report', 'Vietnam merchandise export growth first four months 2018 June 2018 Taking Stock report']
- answer: Vietnam's merchandise export growth from January to October 2017 was 21.3 percent, as reported in the December 2017 Taking Stock report [ts-2017-12:p023:para:003]. In contrast, the export growth for the first four months of 2018 was 19.2 percent, according to the June 2018 report [ts-2018-06:p022:para:001].
- gợi ý: ý đáp án [True, True], context đủ evidence=True
  - [ts-2017-12:p023:para:003] gold-group=['A']: 1.17. improved external demand strengthened Vietnam's already strong export performance. Vietnam's total export turnover between January and October 2017 is estimated at $174.5 billion, up 21.3 percent from the same period last year. Primary commodity exports increased significantly because of a recovery of commodity prices. Crude oil exports rose by 26 percent compared to a substantive decline last year. The export value of agricultural commodities also increased strongly by about 17.5 percent. Manufacturing exports continued to grow
  - [ts-2018-06:p022:para:001] gold-group=['B']: 12. Vietnam's export performance continues to be exceptionally strong, supported by robust export-oriented foreign-invested manufacturing output and improved external demand. Over the first four months of 2018, Vietnamese export growth accelerated 19.2 percent in value terms (y/y). This is mainly due to a combination of robust growth of manufacturing and agriculture exports. Exports of smart phones, which account for nearly 22 percent of total exports in value-terms, expanded by 32.5 percent, sustaining a dynamic pace of growth of over 30 percent achieved in 2017. High value manufacturing exports (smart phones, computers, electronics and cameras) together rose by healthy 25 percent and contr

## n05 · thieu_evidence · filter=None

**Q:** What GDP growth rate does the World Bank forecast for Vietnam in 2021?

**Thiếu evidence:** Dự báo chỉ tới năm 2020. Regex /2021/ không khớp trang nào trong hai PDF.

### `n05|1cad6d07` ← A0_dense_k3_b800, A4_dense_rerank_k5_b4000_repair
- status: **abstain**, searches: ['Vietnam GDP growth rate forecast 2021', 'Vietnam GDP growth forecast 2021']
- answer: The reports do not provide a GDP growth rate forecast for Vietnam in 2021.

## n06 · thieu_evidence · filter=None

**Q:** How much money did the government raise from selling its stake in Sabeco?

**Thiếu evidence:** Regex /Sabeco/ chỉ khớp ts-2017-12 tr.23 (không có số tiền); /proceeds/ chỉ khớp ts-2018-06 tr.9 và 29, không nêu số tiền hay tên doanh nghiệp.

### `n06|f52d6c1f` ← A0_dense_k3_b800
- status: **abstain**, searches: ['government raise money selling stake in Sabeco', 'money raised from selling stake in Sabeco', 'Sabeco stake sale revenue', 'Sabeco stake sale amount raised']
- answer: The evidence does not provide information on the amount of money raised by the government from selling its stake in Sabeco.

### `n06|06844004` ← A4_dense_rerank_k5_b4000_repair
- status: **abstain**, searches: ['government raise money selling stake in Sabeco', 'Sabeco stake sale revenue', 'Sabeco stake sale amount revenue', 'Sabeco stake sale amount revenue government']
- answer: The evidence does not provide specific information on the amount of money raised by the government from selling its stake in Sabeco.

## n07 · thieu_evidence · filter=None

**Q:** By how much did Vietnam raise its regional minimum wage for 2018?

**Thiếu evidence:** Regex /minimum wage|wage floor|basic salary/ không khớp trang nào; /minimum/ chỉ khớp 'minimum quality standards' (ts-2018-06 tr.17); 'base wage' chỉ có trong tiêu đề hình 2.4 về quỹ lương khu vực công (ts-2017-12 tr.42), không phải lương tối thiểu vùng. Báo cáo chỉ nêu tăng trưởng lương bình quân.

### `n07|bf8b8272` ← A0_dense_k3_b800
- status: **abstain**, searches: ['Vietnam regional minimum wage increase 2018', 'Vietnam minimum wage increase 2018']
- answer: The evidence does not provide information on the specific amount by which Vietnam raised its regional minimum wage for 2018.

### `n07|03baa271` ← A4_dense_rerank_k5_b4000_repair
- status: **abstain**, searches: ['Vietnam regional minimum wage increase 2018', 'Vietnam minimum wage increase 2018']
- answer: The evidence does not specify the amount by which Vietnam raised its regional minimum wage for 2018.

