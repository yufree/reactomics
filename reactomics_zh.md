# 反应组学

**反应组学**（Reactomics）是以化学反应为研究对象的系统性学科——具体而言，通过质谱数据中观测到的**配对质量距离（PMD，Paired Mass Distance）**来识别并绘制生物体、环境及化学体系中的反应网络。该概念由于淼等人在2020年发表于 *Communications Chemistry* 的[原始论文](https://doi.org/10.1038/s42004-020-00403-z)中正式提出：同一质谱数据集中两个离子之间的精确质量差，直接编码了连接它们的化学反应信息。

核心思想简单而有力：**两个分子之间固定的质量差对应一类特定的化学反应或生物转化**。通过系统梳理非靶向代谢组学数据中的配对质量距离，无需预先知道化合物的身份，即可重建样品中活跃的反应网络。

本页收录与反应组学及PMD分析相关的文献，每月自动更新。

## 为什么反应组学重要

传统代谢组学工作流程通过鉴定化合物并将其丰度与表型关联来开展研究。这种方法固然有价值，但它将代谢物视为独立实体，而非反应网络中的节点。实际上，代谢物经由酶促反应和自发化学反应不断产生、消耗和转化——它们之间通过反应相互连接。

反应组学通过将**反应关系作为研究对象**来弥补这一不足。与其问"哪些代谢物在组间存在差异"，反应组学更关注"哪些反应在组间存在差异"以及"样品中活跃的反应网络是什么"。这一转变带来了几个重要优势：

- 基于反应的分析对注释缺口更具**鲁棒性**——PMD可针对任意峰对计算，无论峰是否已被注释。
- 反应具有**化学可解释性**——PMD值2.0157（H₂）意味着还原反应；14.0157（CH₂）意味着甲基化或碳链延伸。无需查找表即可读懂网络。
- 反应网络可跨条件、跨物种、跨样品类型进行**比较**，而单纯的代谢物列表往往难以做到。
- 该方法与**生化通路数据库**（KEGG、HMDB反应、Reactome）天然契合，同时在注释不完整时仍可使用。

## 配对质量距离与化学反应

### PMD概念

**配对质量距离（PMD）**是同一质谱数据集中检测到的两个离子之间的精确质量差。例如：

| PMD (Da) | 分子式变化 | 反应类型 |
|----------|-----------|---------|
| 2.0157   | H₂        | 还原 / 加氢 |
| 14.0157  | CH₂       | 甲基化、碳链延伸 |
| 15.9949  | O         | 氧化（单氧） |
| 17.0027  | OH        | 羟基化 |
| 18.0106  | H₂O       | 水合 / 脱水 |
| 28.0313  | C₂H₄      | 乙基化 |
| 42.0106  | C₂H₂O    | 乙酰化 |
| 79.9663  | HPO₃      | 磷酸化 |
| 162.0528 | C₆H₁₀O₅  | 己糖加成（糖基化） |

当两个离子之间的PMD与已知反应匹配时，它们即为该反应底物—产物对的候选。当数据集中发现大量此类配对时，即可推断该反应在所研究的生物或化学体系中处于活跃状态。

### PMD网络

由具有化学意义的PMD连接的离子对构成**PMD网络**。节点为离子（检测到的m/z值），边以PMD（即反应类型）为标注。PMD网络以单一数据结构汇总了样品中完整的反应图景。

PMD网络的关键特性：

- **可从任意非靶向LC-MS数据集计算**，无需注释。
- 节点的度分布反映哪些化合物代谢活性最高。
- 比较不同条件下的PMD网络，可揭示哪些反应被上调或下调，类似差异表达分析。
- 子网络通常对应已知生化通路，为生物学解读提供路径。

PMD网络通过[`pmd` R包](https://yufree.github.io/pmd/)中的`getchain()`函数构建，该函数通过追踪连续PMD边将离子链接成反应链。

## 方法与工具

### PMD计算

PMD分析需要**高精度质量测量**，通常来自Orbitrap或Q-TOF等高分辨率质谱仪器。区分同重素反应（如CO，27.9949 Da vs. C₂H₄，28.0313 Da）所需质量精度约为5 ppm或更优。

工作流程如下：

1. **峰检测** — 从原始LC-MS数据中提取含精确m/z值的峰列表（如使用XCMS、MZmine等工具）。
2. **PMD计算** — 计算所有成对质量差，筛选与已知化学反应匹配的PMD。
3. **网络构建** — 使用`getchain()`构建PMD网络，将离子链接成反应链。
4. **定量分析** — 使用`getreact()`计算各样本中底物—产物强度比值；进行网络分析、差异比较或通路注释。

### 定量反应分析

PMD不仅能识别发生了哪些反应，还能对其进行**定量**：对于任意一对由PMD连接的底物—产物离子，其跨样本的强度比值直接反映该反应的活跃程度。`getreact()`正是为此设计——它计算所有PMD连接离子对在每个样本中的强度比值，输出一个"反应×样本"矩阵，可直接用于下游统计比较。

这使得分析从"哪些反应存在"延伸到"哪些反应在不同条件间存在显著差异"——以反应而非单个代谢物作为分析单元。该方法无需注释：例如，15.9949 Da（加氧）的PMD值可以对数据集中每对相关离子的氧化活性进行定量，而无需事先鉴定化合物身份。

### pmd R包

[`pmd`包](https://cran.r-project.org/package=pmd)提供了反应组学分析在R中的完整实现：

- `getpaired()` — 识别由特定PMD连接的离子对
- `getchain()` — 通过追踪离子列表中的反应链构建PMD网络
- `getreact()` — 计算底物—产物强度比值以定量反应活性，输出"反应×样本"矩阵供统计比较
- `getstd()` — 提取同位素相关离子对用于质量控制
- 可视化函数，用于网络图和反应热图

该包支持正负离子模式数据，并与标准代谢组学工作流程集成。

### PMD数据库与反应列表

反应组学依赖与已知生化反应对应的PMD参考列表。`pmd`包内置了多个数据集：

- **`keggrall`** — 源自KEGG酶催化反应的PMD，含反应方程式和KEGG ID
- **`hmdb`** — 来自HMDB人类代谢物条目的高频PMD
- **`omics`** — 整合多个数据库的反应PMD汇总表，涵盖主要组学反应
- **`sda`** — 亚结构差异、离子替换和反应的常见PMD
- **`MaConDa`** — 质谱污染物PMD，用于背景干扰核查

## 源内反应与独立峰选择

源内反应——加合物形成、源内碎裂和同位素模式——同样会在LC-MS数据集中的离子对之间产生特征性质量差。这些属于分析仪器产生的伪影而非生物反应，但遵循相同的PMD逻辑：两个离子之间固定的质量差编码了连接它们的特定过程。

这一发现是 **globalstd 算法**的核心依据，该算法由[Yu、Olkowicz与Pawliszyn（2019）](https://doi.org/10.1016/j.aca.2018.10.062)提出，并在`pmd`包中实现。globalstd 的关键特点是**数据驱动**：它不依赖预定义的加合物列表，而是从当前数据集中发现哪些质量差真正普遍存在，并以此为据定义冗余。算法分三步执行：

1. **保留时间聚类** — 将共流出离子归为一组，认为它们来源于同一化合物。
2. **数据驱动的高频PMD检测** — 在每个RT组内计算成对质量差。在多个组中高频出现的PMD被推断为**广泛存在的加合物与中性丢失**（如Na/H交换、¹³C同位素、常见溶剂加合物）。由于每个发生同一源内反应的化合物都贡献相同的PMD，这些质量差会积累出异常高的计数——而这一信号完全源自数据本身。
3. **独立峰筛选** — 利用发现的高频PMD，每个化合物簇保留一个代表性离子，去除冗余的加合物、同位素峰和源内碎片。

最终输出一套**无冗余的独立离子集合**，在保留完整化学多样性的同时消除峰的多重性。无需预先了解数据集中会出现哪些加合物。

## 药物代谢应用

药物代谢产生一组可预测的生物转化产物。I相反应（氧化、还原、水解）和II相反应（结合反应）各对应特定PMD。反应组学支持**非靶向药物代谢谱**分析：给定来自药物处理生物体的样品，PMD网络可识别发生了哪些I相和II相转化，无需预先指定目标代谢物。

## 环境转化应用

环境样品包含经历生物和非生物转化的复杂化学物质混合物。通过计算水体、沉积物或生物组织样品的PMD网络，可在不了解母体化合物身份的情况下识别活跃的转化反应。

## 内源性代谢组学应用

在人类和动物代谢组学中，反应组学将测量到的代谢物丰度与产生它们的酶活性相连。血浆或尿液样品的PMD网络反映了生物体的代谢状态——哪些合成代谢和分解代谢反应最为活跃。

## 每月文献集

以下为每月从PubMed收录的反应组学及PMD分析相关新文献。

<!-- MONTHLY_UPDATES_START -->
### 2026-03

- [Frequency-based paired mass distance method revealed the transformation pathway selection of organic compounds during mineralization treatment.](https://doi.org/10.1016/j.watres.2025.125247) *Water research* （2025-12）
<!-- MONTHLY_UPDATES_END -->

## 全部文献

收录自原始论文（2020年）至今所有使用或扩展PMD反应组学的文献，每月更新。

<!-- COLLECTION_START -->
### 配对质量距离与化学反应

- [Role of oxygenation reactions in chlorinated disinfection byproduct formation during vacuum UV/chlorine treatment of reclaimed water.](https://doi.org/10.1016/j.watres.2026.125913) *Water research* (2026)
- [Transformation process and removal mechanism of DOM based on paired mass distance (PMD) analysis in the multi-stage biological contact oxidation process.](https://doi.org/10.1016/j.biortech.2026.134282) *Bioresource technology* (2026)
- [Insights into Contaminant Composition Variations and Reactomics during Wastewater Treatment Processes Based on Nontargeted Analysis and Paired Mass Distance.](https://doi.org/10.1021/acs.est.5c14774) *Environmental science & technology* (2026)
- [Real-world aged microplastics exacerbate antibiotic resistance genes dissemination in anaerobic sludge digestion via enhancing microbial metabolite communication-driven pilus conjugative transfer.](https://doi.org/10.1016/j.watres.2025.125056) *Water research* (2025)
- [Molecular Reactivity in Maternal Pregnancy Blood and Neonatal Dried Blood Spots Is Associated with the Risk of Pediatric Acute Lymphoblastic Leukemia.](https://doi.org/10.1158/1055-9965.EPI-25-0801) *Cancer epidemiology, biomarkers & prevention : a publication of the American Association for Cancer Research, cosponsored by the American Society of Preventive Oncology* (2025)
- [Microbial Physiological Adaptation to Biodegradable Microplastics Drives the Transformation and Reactivity of Dissolved Organic Matter in Soil.](https://doi.org/10.1021/acs.est.5c09633) *Environmental science & technology* (2025)
- [Molecular Humification Mechanisms of Dissolved Organic Matter during Maize Straw Composting Enhanced by Humus Soil Biomaterial: Paired-Molecule Mass Difference Reactomics Analysis Based on FT-ICR MS.](https://doi.org/10.1021/acs.jafc.5c05559) *Journal of agricultural and food chemistry* (2025)
- [Decoding periodate-driven phototransformation of dissolved organic matter in sunlit waters: Multidimensional property shifts and molecular network reconfiguration.](https://doi.org/10.1016/j.watres.2025.124331) *Water research* (2025)
- [Identifying the impacts of photochemical and biological processes on wastewater effluent organic matter in receiving water using directed paired mass distance](https://doi.org/10.1016/j.jece.2025.117411) *Journal of Environmental Chemical Engineering* (2025)
- [Wildfire-Derived Pyrogenic Dissolved Organic Matter (pyDOM) Enhances Riverine DOM Reactivities and Nitrogen Metabolisms.](https://doi.org/10.1021/acs.est.5c01794) *Environmental science & technology* (2025)
- [Toward an integrated omics approach for plant biosynthetic pathway discovery in the age of AI](https://doi.org/10.1016/j.tibs.2025.01.010) *Trends in Biochemical Sciences* (2025)
- [Enhanced Release and Reactivity of Soil Water-Extractable Organic Matter Following Wildfire in a Subtropical Forest.](https://doi.org/10.1021/acs.est.4c13557) *Environmental science & technology* (2025)
- [Revealing the interplay of dissolved organic matters variation with microbial symbiotic network in lime-treated sludge landscaping.](https://doi.org/10.1016/j.envres.2024.120216) *Environmental research* (2024)
- [Complexation with Metal Ions Affects Chlorination Reactivity of Dissolved Organic Matter: Structural Reactomics of Emerging Disinfection Byproducts.](https://doi.org/10.1021/acs.est.4c03022) *Environmental science & technology* (2024)
- [Determination of Sedative and Anesthetic Drug Residues in Aquatic Food Products Using Solid Phase Extraction (SPE) and Liquid Chromatography–Tandem Mass Spectrometry (LC–MS/MS)](https://doi.org/10.1080/00032719.2024.2358160) *Analytical Letters* (2024)
- [Exploring Prenatal Exposure to Halogenated Compounds and Its Relationship with Birth Outcomes Using Nontarget Analysis](https://doi.org/10.1021/acs.est.3c09534) *Environmental Science &amp; Technology* (2024)
- [Inhibitory effect of microplastics derived organic matters on humification reaction of organics in sewage sludge under alkali-hydrothermal treatment.](https://doi.org/10.1016/j.watres.2024.121231) *Water research* (2024)
- [Tracking the transformation pathway of dissolved organic matters (DOMs) in biochars under sludge pyrolysis via reactomics and molecular network analysis.](https://doi.org/10.1016/j.chemosphere.2023.140149) *Chemosphere* (2023)
- [Ring-Opening Polymerization of rac-Lactide Catalyzed by Octahedral Nickel Carboxylate Complexes](https://doi.org/10.3390/catal13020304) *Catalysts* (2023)
- [Comprehensive understanding of DOM reactivity in anaerobic fermentation of persulfate-pretreated sewage sludge via FT-ICR mass spectrometry and reactomics analysis.](https://doi.org/10.1016/j.watres.2022.119488) *Water research* (2022)
- [In vivo solid phase microextraction for bioanalysis](https://doi.org/10.1016/j.trac.2022.116656) *TrAC Trends in Analytical Chemistry* (2022)
- [Recent advances in data-mining techniques for measuring transformation products by high-resolution mass spectrometry](https://doi.org/10.1016/j.trac.2021.116409) *TrAC Trends in Analytical Chemistry* (2021)
- [Single Cell Reactomics: Real-Time Single-Cell Activation Kinetics of Optically Trapped Macrophages.](https://doi.org/10.1002/smtd.202000849) *Small methods* (2021) — Extends reactomics to the single-cell level. Combines optical trapping with PMD-based reaction monitoring to track real-time metabolic activation kinetics in individual macrophages.
- [Untargeted high-resolution paired mass distance data mining for retrieving general chemical relationships.](https://doi.org/10.1038/s42004-020-00403-z) *Communications chemistry* (2020) — The original reactomics paper. Introduces the PMD concept: high-frequency mass differences in untargeted MS data directly encode active chemical reactions, enabling reaction-network reconstruction without compound identification.
- [Carbohydrate fraction characterisation of functional yogurts containing pectin and pectic oligosaccharides through convolutional networks](https://doi.org/10.1016/j.jfca.2020.103484) *Journal of Food Composition and Analysis* (2020)
- [Recent Advances in In Vivo SPME Sampling](https://doi.org/10.3390/separations7010006) *Separations* (2020)
- [Reactomics: using mass spectrometry as a reaction detector](https://doi.org/10.1101/855148) (2019)

### PMD网络

- [Frequency-based paired mass distance method revealed the transformation pathway selection of organic compounds during mineralization treatment.](https://doi.org/10.1016/j.watres.2025.125247) *Water research* (2025) — Uses frequency-based PMD analysis to reveal which transformation pathways are preferentially selected during organic matter mineralisation, linking reaction selectivity to treatment conditions.
- [Microbial Roles in Dissolved Organic Matter Transformation in Full-Scale Wastewater Treatment Processes Revealed by Reactomics and Comparative Genomics.](https://doi.org/10.1021/acs.est.1c02584) *Environmental science & technology* (2021) — Pairs reactomics with comparative genomics. PMD-based reaction networks identify which microbial guilds drive specific dissolved-organic-matter transformations across full-scale wastewater treatment stages.
- [Metabolism of SCCPs and MCCPs in Suspension Rice Cells Based on Paired Mass Distance (PMD) Analysis.](https://doi.org/10.1021/acs.est.0c01830) *Environmental science & technology* (2020) — First application of PMD network to biotransformation tracing. Uses PMD-linked ion chains to map chlorinated paraffin metabolism in rice cells, demonstrating that reaction pathways can be recovered from untargeted data without compound annotation.

### 方法与工具

- [Trends and Innovations in Tools for Processing Chromatographic Data Using Mass Spectrometry Detection: A Systematic Review](https://doi.org/10.1080/10408347.2025.2528134) *Critical Reviews in Analytical Chemistry* (2025)
- [Accurate detection and high throughput profiling of unknown PFAS transformation products for elucidating degradation pathways.](https://doi.org/10.1016/j.watres.2025.123645) *Water research* (2025)
- [Unveiling molecular DOM reactomics and transformation coupled with multifunctional nanocomposites under anaerobic conditions: Tracking potential metabolomics and pathways.](https://doi.org/10.1016/j.chemosphere.2025.144111) *Chemosphere* (2025)
- [Deciphering Microbe-Mediated Dissolved Organic Matter Reactome in Wastewater Treatment Plants Using Directed Paired Mass Distance.](https://doi.org/10.1021/acs.est.3c06871) *Environmental science & technology* (2023)
- [Interpretable Machine Learning and Reactomics Assisted Isotopically Labeled FT-ICR-MS for Exploring the Reactivity and Transformation of Natural Organic Matter during Ultraviolet Photolysis.](https://doi.org/10.1021/acs.est.3c05213) *Environmental science & technology* (2023)
- [A multiplatform metabolomics/reactomics approach as a powerful strategy to identify reaction compounds generated during hemicellulose hydrothermal extraction from agro-food biomasses.](https://doi.org/10.1016/j.foodchem.2023.136150) *Food chemistry* (2023)
- [A Novel LC-MS Based Targeted Metabolomic Approach to Study the Biomarkers of Food Intake.](https://doi.org/10.1002/mnfr.202000615) *Molecular nutrition & food research* (2020)

### 源内反应与独立峰选择

- [Reproducible untargeted metabolomics workflow for exhaustive MS2 data acquisition of MS1 features.](https://doi.org/10.1186/s13321-022-00586-8) *Journal of cheminformatics* (2022)
- [Metabolic profile of fish muscle tissue changes with sampling method, storage strategy and time.](https://doi.org/10.1016/j.aca.2020.08.050) *Analytica chimica acta* (2020)
- [Prediction of response after chemoradiation for esophageal cancer using a combination of dosimetry and CT radiomics.](https://doi.org/10.1007/s00330-019-06193-w) *European radiology* (2019)
- [Structure/reaction directed analysis for LC-MS based untargeted analysis.](https://doi.org/10.1016/j.aca.2018.10.062) *Analytica chimica acta* (2018) — Introduces the globalstd algorithm for data-driven independent ion selection. High-frequency PMDs among co-eluting peaks reveal widespread adducts and neutral losses; one representative ion per compound is retained, eliminating redundancy without a predefined adduct list.

### 药物代谢应用

- [Active Molecular Network Discovery Links Lifestyle Variables to Breast Cancer in the Long Island Breast Cancer Study Project.](https://doi.org/10.1021/envhealth.3c00218) *Environment & health (Washington, D.C.)* (2024)
- [Mapping the metabolic responses to oxaliplatin-based chemotherapy with in vivo spatiotemporal metabolomics.](https://doi.org/10.1016/j.jpha.2023.08.001) *Journal of pharmaceutical analysis* (2023)
- [Metabolomic fingerprinting of porcine lung tissue during pre-clinical prolonged ex vivo lung perfusion using in vivo SPME coupled with LC-HRMS.](https://doi.org/10.1016/j.jpha.2022.06.002) *Journal of pharmaceutical analysis* (2022)
- [Molecular Gatekeeper Discovery: Workflow for Linking Multiple Exposure Biomarkers to Metabolomics.](https://doi.org/10.1021/acs.est.1c04039) *Environmental science & technology* (2022) — Introduces the molecular gatekeeper concept. Uses PMD analysis to link multiple environmental exposure biomarkers to downstream metabolomics, identifying hub metabolites that mediate exposure–health relationships.
- [Compartmentalization and Excretion of 2,4,6-Tribromophenol Sulfation and Glycosylation Conjugates in Rice Plants.](https://doi.org/10.1021/acs.est.0c07184) *Environmental science & technology* (2021)

### 环境转化应用

- [FT-ICR MS and viral metagenomics reveal distinct mechanisms of lysogenic and lytic phage-driven DOM transformations in wastewater at formula-levels](https://doi.org/10.1016/j.cej.2025.167655) *Chemical Engineering Journal* (2025)
- [Transformative Forces: The Role of Gut Microbiota in Processing Environmental Pollutants](https://doi.org/10.1021/acs.est.5c01928) *Environmental Science &amp; Technology* (2025)
- [Reaction Sequence of the UV/H<sub>2</sub>O<sub>2</sub> System on the Suwannee River Dissolved Organic Matter with Complex Molecular Composition](https://doi.org/10.1021/acsestwater.4c01260) *ACS ES&amp;T Water* (2025)
- [MoleTrans: Browser-Based Webtool for Postanalysis on Molecular Chemodiversity and Transformation of Dissolved Organic Matters via FT-ICR MS](https://doi.org/10.1021/acs.estlett.5c00284) *Environmental Science &amp; Technology Letters* (2025)
- [Integrating machine learning, suspect and nontarget screening reveal the interpretable fates of micropollutants and their transformation products in sludge](https://doi.org/10.1016/j.jhazmat.2025.137183) *Journal of Hazardous Materials* (2025)
- [Effect of a high Cl– concentration on the transformation of waste leachate DOM by the UV/PMS system: A mechanistic study using the Suwannee River natural organic matter (SRNOM) as a simulator of waste leachate DOM](https://doi.org/10.1016/j.jhazmat.2024.137038) *Journal of Hazardous Materials* (2025)
- [Long-term fertilization promotes the microbial-mediated transformation of soil dissolved organic matter](https://doi.org/10.1038/s43247-025-02032-7) *Communications Earth &amp; Environment* (2025)
- [Photochemical transformation altered coagulation behavior and treatability of dissolved organic matters in water](https://doi.org/10.1016/j.seppur.2024.128536) *Separation and Purification Technology* (2025)
- [Network-Based Methods for Deciphering the Oxidizability of Complex Leachate DOM with <sup>•</sup>OH/O<sub>3</sub> via Molecular Signatures](https://doi.org/10.1021/acs.est.4c08840) *Environmental Science &amp; Technology* (2025)
- [DNEA: an R package for fast and versatile data-driven network analysis of metabolomics data.](https://doi.org/10.1186/s12859-024-05994-1) *BMC bioinformatics* (2024)
- [The impact of sampling time point on the lipidome composition](https://doi.org/10.1016/j.jpba.2024.116429) *Journal of Pharmaceutical and Biomedical Analysis* (2024)
- [Enhanced removal of biolabile oxygen-depleted dissolved organic matter by coagulation-adsorption process Improves biological stability of reclaimed water](https://doi.org/10.1016/j.cej.2024.157156) *Chemical Engineering Journal* (2024)
- [Machine learning-enhanced molecular network reveals global exposure to hundreds of unknown PFAS.](https://doi.org/10.1126/sciadv.adn1039) *Science advances* (2024)
- [Unveiling intricate transformation pathways of emerging contaminants during wastewater treatment processes through simplified network analysis](https://doi.org/10.1016/j.watres.2024.121299) *Water Research* (2024)
- [Exploring the Complexities of Dissolved Organic Matter Photochemistry from the Molecular Level by Using Machine Learning Approaches](https://doi.org/10.1021/acs.est.3c00199) *Environmental Science &amp; Technology* (2023)
- [Synchronous biostimulants recovery and dewaterability enhancement of anaerobic digestion sludge through post-hydrothermal treatment](https://doi.org/10.1016/j.cej.2023.141881) *Chemical Engineering Journal* (2023)
- [Bioaccumulation and Biotransformation of Chlorinated Paraffins.](https://doi.org/10.3390/toxics10120778) *Toxics* (2022)
- [Strategies for structure elucidation of small molecules based on LC-MS/MS data from complex biological samples.](https://doi.org/10.1016/j.csbj.2022.09.004) *Computational and structural biotechnology journal* (2022)
- [Novel insight into dissolved organic nitrogen (DON) transformation along wastewater treatment processes with special emphasis on endogenous-source DON.](https://doi.org/10.1016/j.envres.2022.112713) *Environmental research* (2022)
- [In Vivo Solid-Phase Microextraction and Applications in Environmental Sciences.](https://doi.org/10.1021/acsenvironau.1c00024) *ACS environmental Au* (2021)
- [Tooth biomarkers to characterize the temporal dynamics of the fetal and early-life exposome.](https://doi.org/10.1016/j.envint.2021.106849) *Environment international* (2021)
- [Medium- and Short-Chain Chlorinated Paraffins in Mature Maize Plants and Corresponding Agricultural Soils.](https://doi.org/10.1021/acs.est.0c05111) *Environmental science & technology* (2021)
- [In Vivo SPME for Bioanalysis in Environmental Monitoring and Toxicology](https://doi.org/10.1007/978-981-13-9447-8_3) *A New Paradigm for Environmental Chemistry and Toxicology* (2019)

### 内源性代谢组学应用

- [mzrtsim: Raw Data Simulation for Reproducible Gas/Liquid Chromatography–Mass Spectrometry-Based Nontargeted Metabolomics Data Analysis](https://doi.org/10.1021/acs.analchem.5c01213) *Analytical Chemistry* (2025)
- [mzrtsim: Raw Data Simulation for Reproducible Gas/Liquid Chromatography–Mass Spectrometry Based Non-targeted Metabolomics Data Analysis](https://doi.org/10.1101/2023.11.14.567024) (2023)
- [Deep Characterization of Serum Metabolome Based on the Segment-Optimized Spectral-Stitching Direct-Infusion Fourier Transform Ion Cyclotron Resonance Mass Spectrometry Approach](https://doi.org/10.1021/acs.analchem.2c04995) *Analytical Chemistry* (2023)
- [A mass defect filtering combined background subtraction strategy for rapid screening and identification of metabolites in rat plasma after oral administration of Yindan Xinnaotong soft capsule](https://doi.org/10.1016/j.jpba.2023.115400) *Journal of Pharmaceutical and Biomedical Analysis* (2023)
- [AI/ML-driven advances in untargeted metabolomics and exposomics for biomedical applications.](https://doi.org/10.1016/j.xcrp.2022.100978) *Cell reports. Physical science* (2022)
- [Metabolite discovery through global annotation of untargeted metabolomics data.](https://doi.org/10.1038/s41592-021-01303-3) *Nature methods* (2021) — NetID uses global network optimisation for metabolite annotation. Incorporates PMD-based ion relationships to propagate identities from known to unannotated LC-MS peaks across the full dataset.
- [Untargeted metabolomics profiling and hemoglobin normalization for archived newborn dried blood spots from a refrigerated biorepository.](https://doi.org/10.1016/j.jpba.2020.113574) *Journal of pharmaceutical and biomedical analysis* (2020)
- [A UPLC-Q-TOF-MS-based metabolomics approach for the evaluation of fermented mare’s milk to koumiss](https://doi.org/10.1016/j.foodchem.2020.126619) *Food Chemistry* (2020)
- [Simulation-based comprehensive study of batch effects in metabolomics studies](https://doi.org/10.1101/2019.12.16.878637) (2019)
- [The metaRbolomics Toolbox in Bioconductor and beyond.](https://doi.org/10.3390/metabo9100200) *Metabolites* (2019)

*共 79 篇论文。最后更新：2026-04-28。*
<!-- COLLECTION_END -->

## 月度存档

<!-- MONTHLY_ARCHIVE_START -->
- [2026-03](updates/2026-03.html) — 1 篇论文
<!-- MONTHLY_ARCHIVE_END -->
