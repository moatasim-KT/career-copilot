# Lazy-Loaded Components

This directory contains lazy-loaded wrappers for heavy components to improve initial bundle size and loading performance through code splitting.

## Overview

Code splitting allows us to split our application into smaller chunks that can be loaded on demand. This is especially important for:

- **Heavy libraries** (Recharts, react-grid-layout, cmdk)
- **Complex components** (AdvancedSearch, QueryBuilder)
- **Conditionally rendered features** (CommandPalette, NotificationCenter)

## Benefits

1. **Reduced Initial Bundle Size**: Heavy components are not included in the main bundle
2. **Faster Initial Load**: Users download less JavaScript upfront
3. **Better Performance**: Components load only when needed
4. **Improved User Experience**: Loading skeletons provide visual feedback

## Available Lazy Components

### Page Components

#### LazyAnalyticsPage
Lazy-loads the AnalyticsPage with Recharts library (~100KB).

```tsx
import { LazyAnalyticsPage } from '@/components/lazy';

export default function AnalyticsRoute() {
  return <LazyAnalyticsPage />;
}
```

#### LazyEnhancedDashboard
Lazy-loads the EnhancedDashboard with react-grid-layout (~50KB).

```tsx
import { LazyEnhancedDashboard } from '@/components/lazy';

export default function DashboardRoute() {
  return <LazyEnhanced
e/)formancweb.dev/pers](https://acticece Best Prrforman [Web Peact/lazy)
-rev/reference/ct.de//reang](https:ode Splittieact C
- [Rport)amic-imes/dynfeaturced-vanorg/docs/ad//nextjs.https:orts](c ImpDynami[Next.js ion

- entatd Docum
## Relateer
for PDF viewng lazy loadiplement 
- [ ] Imgalleriesor image zy loading f] Add lalits
- [ t spmponenhart cor cgranulareate more 
- [ ] C componentslazyfor daries  error boun[ ] Addcharts
- ading for ve loessigrmplement procus
- [ ] Ifoon hover/nts componech lazy Prefet[ ] ts

-  Enhancemen

## Futurertrect impof did instead oeing use bcomponent islazy Verify  split
4. tovy enough actually heat is e componenes
3. Ensur sizunktab for check Network Chtting
2.  verify splilyzer toanan bundle Rug

1.  Improvinformance Not

### Per usedbeingnly APIs r client-o Check foe
3.cturrucomponent sttches final keleton maure s Ensort
2.impic amse` in dynfal `ssr: 
1. Settches:maation misdru see hy
If yo
rrorsHydration E# 
##t
ry is presenpense boundak SusChecy
4. ted correctl is expornentre compo. Ensu
3k loadinghows chun saby network t
2. Verif errorsnsole fork browser co
1. Chec
 Not Loadingonent# Comping

##ubleshootro`

## T
}
``icsPage />;yAnalyteturn <Laz r {
 ics()lytn Anault functioxport defazy';

eents/laom '@/componge } frcsPaazyAnalyti
import { L
```tsxport)
azy Im After (L

###
```age />;
}lyticsPeturn <Ana
  rlytics() {ion Anaefault funct
export d;
ticsPage'/Analyents/pages'@/componge from icsPat Analyt`tsx
import)

``ect Imporfore (Dirde

### BeGuiration 
## Mig
```
;={isOpen} />ent isOpenomponrn <LazyCretull
}

mponent at an't load co; // Dorn nullretu {
  (!isOpen)
if :

```tsx openedil they'reg untdint loa, we prevenonents compdownodal/drop
For mg
Loadinditional 

### Conpense>
```>
</Sust /onenomp
  <LazyCkeleton />}>back={<Sspense fall
```tsx
<Suck:
allbath a fdary wiense bouna Suspapped in s wr i componentzyach laries

Ee Bounda Suspens

###
```e APIs
});-sideds clientt neen if componDisable SSR// false, />,
  ssr: n Skeleto () => <g:adinlont'), {
  mponeimport('./Conamic(() => mponent = dysx
const Co

```tration:tter integbe for lazy()eact.tead of Rnsc()` ijs `dynami use Next.
Weort
c Impxt.js Dynamis

### Nen DetailentatioplemIm

## tial bundleKB from inings**: ~200tal savi
**To
undle |from main b0KB | ~30KB | -3ancedSearch  |
| Adv main bundlefrom| -20KB | ~20KB  cmdk undle |
|from main b | -50KB | ~50KBlayout rid-t-gace |
| re main bundl-100KB from | ~100KB | ts|
| Rechar-----------------|--------|------|-------act |
 Imp Load Initiale | Sizonent |:

| Compdinglazy loaments with rove impted
Expecics
ormance Metr# Perf`

#
``nalyzenpm run a


```bashorking:litting is wde spto verify cole analyzer Use the bundizes

or Bundle SMonit 5. izes

### screen s Differentisabled
- Cache dtling
-etwork throtG nw 3 Slots with:
-ponenour lazy coms

Test ying Stateadest Lo 4. T

###contenthe-fold ove-tabritical  C visible
- alwayshat areomponents t
- C10KB)(<nts mpone Small cooad:
-'t lazy-lg

Donlittind Over-Sp## 3. Avoiyout.

#ponent's lae final comt match thnents thaompoeton cskelate propriays use ap

Alwsg Stateoadinod Lvide Go### 2. Proies

brarrty liird-pay th- Use heavy rendered
tionall Condile
-visibely ediat)
- Not imm>20KBge in size (- Lar that are:
 components-load

Only lazytsy Componenfor Heav. Use ### 1es

actic Pr# Best

#data tables For leton` -SkebleataTa`Dts
- ouoard layFor dashb- Skeleton`  `Dashboardopdown
-fication dror notileton` - FnCenterSketiootificael
- `Nd search panr advance` - FochSkeletondvancedSear
- `Aletter command paFoeleton` - aletteSkndP
- `Commarea charts/a - For lineeleton`neChartSk `Li
-tsharnut cie/door peleton` - F `PieChartSks
-posed chartr/comn` - For baeleto- `ChartSk

s loading:t iual componene act th whileays displatcomponent thskeleton ding onas a correspponent homy cch laz
Eaeletons
ng Sk

## Loadi);
}
```er>
  hartWrapp
    </C}ent */hart componur c      {/* Yo"line">
per type=  <ChartWrapeturn (
    rhart() {
unction MyC';

fs/lazy@/componentr } from 'ChartWrappeimport { 

```tsx
hart Wrapper`

#### C
}
``iner>
  );siveConta    </ResponChart>
LazyPie     </*/}
 guration hart confi  {/* C      PieChart>
      <Lazy{300}>
ght=" hei="100%iner widthContaResponsive
    <(n   retur() {
usChartatction Stts;

funhartComponenyC= LazTooltip } s, YAxier, XAxis, ntainResponsiveCo { 

constlazy';s/component@/ from 's 
}mponenttCo
  LazyCharyLineChart,
  LazBarChart, 
  LazyyPieChart,  Lazmport { 
 `tsx
i Types

``al Chart## Individu

##nentshart Compo``

### C  );
}
`
    />
tes..."te your noder="Wri   placeholnt}
   ntehange={setCo     onC{content}
     value=tEditor
  ex<LazyRichTturn (
     
  re');
 eState('t] = usetConten st [content, {
  consor()eEdit Not
function
ents/lazy'; '@/compon fromextEditor }LazyRichTt { sx
imporn).

```tntatioure implemefor futolder or (placehxt editch te ridsLazy-loaTextEditor
LazyRich``

#### 
  );
}
`ing
    />er  enableFiltg
    rtin  enableSoa}
    data={dat     umns}
 lumns={col     coTable
 Datazyn (
    <Laur) {
  rete(obsTabl
function Jy';
ponents/lazcomm '@/ro } ftaTableort { LazyDa
```tsx
imp
ag-and-drop.for drkit e with dnd-the DataTabl-loads 
LazytaTable## LazyDanents

### UI Compo

##
}
``` />
  );lse)} 
   etIsOpen(fa={() => s     onClose
 en={isOpen}     isOpenter 
  icationC <LazyNotif
    return (lse);
  
 eState(fan] = uspetIsO[isOpen, se {
  const Navigation()n 
functios/lazy';
ent '@/componter } fromationCentificort { LazyNo
imp
```tsxdown.
roponCenter dficatiNotis the azy-load
LntertificationCeNo### Lazy`

#
  );
}
``
    />s}eldFirch{seafields=      ry)}
(queconsole.logy) => earch={(quer onS     en(false)}
sOp() => setIse={   onClo
   isOpen}   isOpen={arch
   AdvancedSe<Lazy (
     
  return
 se);ate(fal = useStsOpen]etIisOpen, sonst [) {
  ce(rchPagion Sea';

functponents/lazyom '@/comarch } frdvancedSeort { LazyA`tsx
imp
``Builder.
 Queryel withearch panancedS the Advazy-loadsch
LcedSearLazyAdvan
#### rue.
pen` is ten `isOly loads whonent onote**: Comp``

**N
  );
}
`    />lse)} 
tIsOpen(fa> see={() =nClos
      open} en={isO
      isOptte CommandPale(
    <Lazy  return alse);
  
 useState(fIsOpen] =etOpen, sst [ison) {
  ction App(y';

funcmponents/laz/coom '@fre } andPalett { LazyCommimportx

```ts~20KB).
ry (brak lite with cmdaletndPhe Commaloads tlette
Lazy-dPamanLazyCom# 
###s
e Component Featur
```

###ard />;
}Dashbo