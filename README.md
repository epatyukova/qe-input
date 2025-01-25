# 💬 QE input generation

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://qe-input-uz9q3ttmkku766bnzkvygr.streamlit.app/)

This application is a product of the STFC **Goldilocks** project. The purpose if this 
app is to help unexperienced user to setup single point SCF energy calculation with 
Quantum Espresso package [1,2] and SSSP library of pseudo-potentials [3]. 
            
DFT calculations contain numerical approximations that need to be
converged according to the accuracy required for each study. Here to save compute time 
(and by this make computations more sustainable) we predict these parameters with 
ML models trained on a database of converged SCF calculations performed before [7,8]. 
            
To facilitate understanding of the content of the input file we provide an integration 
of the LLMs [9] helping to answer users questions about the content of the input file, 
or provide user-requested changes to parameters.

### How to run it on your own machine

1. Install the requirements

   ```
   $ pip install -r requirements.txt
   ```

2. Run the app

   ```
   $ streamlit run src/qe_input/QE_input_generation_app.py
   ```

**References**

[1] *Advanced capabilities for materials modelling with Quantum ESPRESSO* 
   P Giannozzi, O Andreussi, T Brumme, O Bunau, M Buongiorno Nardelli, 
   M Calandra, R Car, C Cavazzoni, D Ceresoli, M Cococcioni, N Colonna, I Carnimeo, 
   A Dal Corso, S de Gironcoli, P Delugas, R A DiStasio Jr, A Ferretti, A Floris, 
   G Fratesi, G Fugallo, R Gebauer, U Gerstmann, F Giustino, T Gorni, J Jia, 
   M Kawamura, H-Y Ko, A Kokalj, E Küçükbenli, M Lazzeri, M Marsili, N Marzari, 
   F Mauri, N L Nguyen, H-V Nguyen, A Otero-de-la-Roza, L Paulatto, S Poncé, D Rocca, 
   R Sabatini, B Santra, M Schlipf, A P Seitsonen, A Smogunov, I Timrov, T Thonhauser, 
   P Umari, N Vast, X Wu and S Baroni, J.Phys.:Condens.Matter 29, 465901 (2017)

[2] *QUANTUM ESPRESSO: a modular and open-source software project for quantum simulations of materials* 
   P. Giannozzi, S. Baroni, N. Bonini, M. Calandra, R. Car, C. Cavazzoni, D. Ceresoli, 
   G. L. Chiarotti, M. Cococcioni, I. Dabo, A. Dal Corso, S. Fabris, G. Fratesi, 
   S. de Gironcoli, R. Gebauer, U. Gerstmann, C. Gougoussis, A. Kokalj, M. Lazzeri, 
   L. Martin-Samos, N. Marzari, F. Mauri, R. Mazzarello, S. Paolini, A. Pasquarello, 
   L. Paulatto, C. Sbraccia, S. Scandolo, G. Sclauzero, A. P. Seitsonen, A. Smogunov, 
   P. Umari, R. M. Wentzcovitch, J. Phys. Condens. Matter 21, 395502 (2009)

[3] *Precision and efficiency in solid-state pseudopotential calculations* 
   G. Prandini, A. Marrazzo, I. E. Castelli, N. Mounet and N. Marzari, 
   npj Computational Materials 4, 72 (2018), http://materialscloud.org/sssp
            
[4] *The atomic simulation environment—a Python library for working with atoms*.
   Ask Hjorth Larsen, Jens Jørgen Mortensen, Jakob Blomqvist, Ivano E Castelli,  
   Rune Christensen, Marcin Dułak, Jesper Friis, Michael N Groves, Bjørk Hammer, 
   Cory Hargus, Eric D Hermes, Paul C Jennings, Peter Bjerre Jensen, 
   James Kermode, John R Kitchin, Esben Leonhard Kolsbjerg, 
   Joseph Kubal, Kristen Kaasbjerg, Steen Lysgaard, Jón Bergmann Maronsson, 
   Tristan Maxson, Thomas Olsen, Lars Pastewka, Andrew Peterson, Carsten Rostgaard, 
   Jakob Schiøtz, Ole Schütt, Mikkel Strange, Kristian S Thygesen, Tejs Vegge, 
   Lasse Vilhelmsen, Michael Walter, Zhenhua Zeng and Karsten W Jacobsen 
   2017 J. Phys.: Condens. Matter 29 273002

[5] *Python Materials Genomics (pymatgen) : A Robust,
   Open-Source Python Library for Materials Analysis.* 
   Shyue Ping Ong, William Davidson Richards, Anubhav Jain, Geoffroy Hautier,
   Michael Kocher, Shreyas Cholia, Dan Gunter, Vincent Chevrier, Kristin A.
   Persson, Gerbrand Ceder. Computational Materials
   Science, 2013, 68, 314–319. https://doi.org/10.1016/j.commatsci.2012.10.028 

[6] *Commentary: The Materials Project: A materials genome approach to accelerating materials innovation* 
   Anubhav Jain, Shyue Ping Ong, Geoffroy Hautier, Wei Chen, William Davidson Richards, 
   Stephen Dacek, Shreyas Cholia, Dan Gunter, David Skinner, Gerbrand Ceder, and Kristin A. Persson

[7] *The joint automated repository for various integrated simulations (JARVIS) for data-driven materials design* 
   Choudhary, K., Garrity, K.F., Reid, A.C.E. et al. npj Computational Materials 6, 173 (2020) https://doi.org/10.1038/s41524-020-00440-1
   We use the partial copy of dft3d dataset to query the structures by formula.

[8] *Materials Cloud three-dimensional crystals database (MC3D)* Sebastiaan Huber, Marnik Bercx, Nicolas Hörmann, Martin Uhrin, Giovanni Pizzi, Nicola Marzari, 
Materials Cloud Archive 2022.38 (2022), https://doi.org/10.24435/materialscloud:rw-t0

[9] To provide reference and advise we suggest to use *OpenAI* models, see usage conditions https://openai.com/policies/row-terms-of-use/ 